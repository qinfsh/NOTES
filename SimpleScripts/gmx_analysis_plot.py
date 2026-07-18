#!/usr/bin/env python3
"""
GROMACS 分析可视化脚本
支持：
1. RMSD
2. RMSF
3. 回旋半径 Rg
4. 自由能景观 FEL（二维等高线 + 三维形貌图）
依赖：
    numpy
    matplotlib
示例：
    python gmx_analysis_plot.py rmsd -f rmsd.xvg -o rmsd.png
    python gmx_analysis_plot.py rmsf -f rmsf.xvg -o rmsf.png
    python gmx_analysis_plot.py rg -f gyrate.xvg -o rg.png
    python gmx_analysis_plot.py fel --x rmsd.xvg --y gyrate.xvg \
        --xlabel "RMSD (nm)" --ylabel "Rg (nm)" --prefix fel

若自由能变量已在同一个三列文件中：
    第1列为时间，第2列为CV1，第3列为CV2
    python gmx_analysis_plot.py fel -f cv_data.xvg --xcol 1 --ycol 2 --prefix fel
"""


import argparse
from pathlib import Path
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm


def read_xvg(path):
    """读取 GROMACS XVG，自动忽略 # 和 @ 注释行。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")

    rows = []
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith(("#", "@")):
                continue
            try:
                rows.append([float(v) for v in line.split()])
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"{path} 中没有可读取的数值数据。")

    data = np.asarray(rows, dtype=float)
    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"{path} 至少应包含两列数值。")
    return data


def configure_style():
    """统一论文绘图风格，不依赖 Arial。"""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.linewidth": 1.2,
        "axes.labelsize": 13,
        "axes.titlesize": 14,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 4,
        "ytick.major.size": 4,
        "xtick.major.width": 1.0,
        "ytick.major.width": 1.0,
        "legend.frameon": False,
        "savefig.dpi": 600,
    })


def moving_average(y, window):
    if window <= 1:
        return y
    if window > len(y):
        raise ValueError("平滑窗口大于数据点总数。")
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(y, kernel, mode="valid")


def plot_series(args, default_ylabel, default_color, default_title):
    data = read_xvg(args.file)
    if args.ycol >= data.shape[1]:
        raise ValueError(
            f"指定的 y 列索引 {args.ycol} 超出范围；文件仅有 {data.shape[1]} 列。"
        )

    x = data[:, args.xcol]
    y = data[:, args.ycol]

    if args.smooth > 1:
        y = moving_average(y, args.smooth)
        x = x[args.smooth - 1:]

    fig, ax = plt.subplots(figsize=(args.width, args.height))
    ax.plot(x, y, color=args.color or default_color, linewidth=args.linewidth)

    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel or default_ylabel)

    if args.title:
        ax.set_title(args.title)
    elif args.show_default_title:
        ax.set_title(default_title)

    ax.set_xlim(np.nanmin(x), np.nanmax(x))

    if args.ymin is not None or args.ymax is not None:
        lo, hi = ax.get_ylim()
        ax.set_ylim(
            args.ymin if args.ymin is not None else lo,
            args.ymax if args.ymax is not None else hi,
        )

    ax.tick_params(direction="in")
    fig.tight_layout()
    fig.savefig(args.output, bbox_inches="tight")
    plt.close(fig)
    print(f"已生成：{Path(args.output).resolve()}")


def align_by_time(data_x, data_y, xcol, ycol):
    """
    按最短长度对齐两个轨迹。
    对常规同源轨迹足够稳健；如时间采样不一致，建议预先统一采样频率。
    """
    x = data_x[:, xcol]
    y = data_y[:, ycol]
    n = min(len(x), len(y))
    if len(x) != len(y):
        print(
            f"警告：两个输入长度不同，将按前 {n} 个点进行配对。",
            file=sys.stderr,
        )
    return x[:n], y[:n]


def compute_fel(x, y, bins, temperature, pseudocount):
    """
    计算二维自由能：
        G = -k_B T ln(P/Pmax)
    单位：kJ/mol
    """
    hist, x_edges, y_edges = np.histogram2d(x, y, bins=bins)
    hist = hist.T

    prob = hist + pseudocount
    prob = prob / np.sum(prob)

    k_b = 0.008314462618  # kJ mol^-1 K^-1
    prob_max = np.max(prob)
    free_energy = -k_b * temperature * np.log(prob / prob_max)

    x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    X, Y = np.meshgrid(x_centers, y_centers)

    return X, Y, free_energy, hist


def plot_fel(args):
    if args.file:
        data = read_xvg(args.file)
        if args.xcol >= data.shape[1] or args.ycol >= data.shape[1]:
            raise ValueError(
                f"输入文件只有 {data.shape[1]} 列，"
                f"无法读取 xcol={args.xcol}, ycol={args.ycol}。"
            )
        x = data[:, args.xcol]
        y = data[:, args.ycol]
    else:
        if not args.x or not args.y:
            raise ValueError("FEL 必须提供 -f，或同时提供 --x 和 --y。")
        data_x = read_xvg(args.x)
        data_y = read_xvg(args.y)
        x, y = align_by_time(data_x, data_y, args.xcol, args.ycol)

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    if len(x) < 10:
        raise ValueError("有效数据点太少，无法计算自由能景观。")

    X, Y, G, hist = compute_fel(
        x=x,
        y=y,
        bins=args.bins,
        temperature=args.temperature,
        pseudocount=args.pseudocount,
    )

    if args.max_energy is not None:
        G_plot = np.minimum(G, args.max_energy)
    else:
        G_plot = G

    prefix = Path(args.prefix)
    contour_path = prefix.with_name(prefix.name + "_2D.png")
    surface_path = prefix.with_name(prefix.name + "_3D.png")
    data_path = prefix.with_name(prefix.name + "_grid.dat")

    # 二维等高线图
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    levels = np.linspace(
        float(np.nanmin(G_plot)),
        float(np.nanmax(G_plot)),
        args.levels,
    )
    contour = ax.contourf(
        X,
        Y,
        G_plot,
        levels=levels,
        cmap=args.cmap,
    )
    ax.contour(
        X,
        Y,
        G_plot,
        levels=levels[::max(1, len(levels) // 10)],
        linewidths=0.35,
        colors="k",
        alpha=0.35,
    )
    cbar = fig.colorbar(contour, ax=ax, pad=0.03)
    cbar.set_label("Free energy (kJ/mol)")

    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    if args.title:
        ax.set_title(args.title)
    ax.tick_params(direction="in")
    fig.tight_layout()
    fig.savefig(contour_path, bbox_inches="tight")
    plt.close(fig)

    # 三维自由能形貌图
    fig = plt.figure(figsize=(6.2, 5.0))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(
        X,
        Y,
        G_plot,
        cmap=args.cmap,
        linewidth=0,
        antialiased=True,
        rcount=min(args.surface_resolution, G_plot.shape[0]),
        ccount=min(args.surface_resolution, G_plot.shape[1]),
    )
    ax.set_xlabel(args.xlabel, labelpad=8)
    ax.set_ylabel(args.ylabel, labelpad=8)
    ax.set_zlabel("Free energy (kJ/mol)", labelpad=8)
    if args.title:
        ax.set_title(args.title)
    ax.view_init(elev=args.elev, azim=args.azim)
    fig.colorbar(surf, ax=ax, shrink=0.65, pad=0.12)
    fig.tight_layout()
    fig.savefig(surface_path, bbox_inches="tight")
    plt.close(fig)

    # 保存网格数据，便于 Origin 或其他软件再绘制
    flat = np.column_stack((X.ravel(), Y.ravel(), G.ravel(), hist.ravel()))
    np.savetxt(
        data_path,
        flat,
        header="CV1 CV2 FreeEnergy_kJ_per_mol Count",
        fmt="%.8f",
    )

    print(f"已生成二维自由能图：{contour_path.resolve()}")
    print(f"已生成三维形貌图：{surface_path.resolve()}")
    print(f"已保存自由能网格：{data_path.resolve()}")


def add_common_series_args(parser, ylabel):
    parser.add_argument("-f", "--file", required=True, help="输入 XVG 文件")
    parser.add_argument("-o", "--output", required=True, help="输出图片文件")
    parser.add_argument("--xcol", type=int, default=0, help="X 数据列索引，默认0")
    parser.add_argument("--ycol", type=int, default=1, help="Y 数据列索引，默认1")
    parser.add_argument("--xlabel", default="Simulation Time (ns)")
    parser.add_argument("--ylabel", default=ylabel)
    parser.add_argument("--title", default="")
    parser.add_argument(
        "--show-default-title",
        action="store_true",
        help="未设置 --title 时显示默认标题",
    )
    parser.add_argument("--color", default=None)
    parser.add_argument("--linewidth", type=float, default=1.2)
    parser.add_argument("--smooth", type=int, default=1)
    parser.add_argument("--ymin", type=float, default=None)
    parser.add_argument("--ymax", type=float, default=None)
    parser.add_argument("--width", type=float, default=4.5)
    parser.add_argument("--height", type=float, default=3.5)


def build_parser():
    parser = argparse.ArgumentParser(
        description="GROMACS RMSD、RMSF、Rg 与自由能景观可视化工具"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_rmsd = sub.add_parser("rmsd", help="绘制 RMSD")
    add_common_series_args(p_rmsd, "RMSD (nm)")
    p_rmsd.set_defaults(
        func=lambda a: plot_series(
            a,
            default_ylabel="RMSD (nm)",
            default_color="#F08080",
            default_title="RMSD",
        )
    )

    p_rmsf = sub.add_parser("rmsf", help="绘制 RMSF")
    add_common_series_args(p_rmsf, "RMSF (nm)")
    p_rmsf.set_defaults(
        xlabel="Residue Number",
        func=lambda a: plot_series(
            a,
            default_ylabel="RMSF (nm)",
            default_color="#6FA8DC",
            default_title="RMSF",
        )
    )

    p_rg = sub.add_parser("rg", help="绘制回旋半径")
    add_common_series_args(p_rg, "Radius of gyration (nm)")
    p_rg.set_defaults(
        func=lambda a: plot_series(
            a,
            default_ylabel="Radius of gyration (nm)",
            default_color="#70AD47",
            default_title="Radius of Gyration",
        )
    )

    p_fel = sub.add_parser("fel", help="绘制二维和三维自由能景观")
    p_fel.add_argument(
        "-f",
        "--file",
        default=None,
        help="包含CV1和CV2的同一个文件",
    )
    p_fel.add_argument("--x", default=None, help="CV1 XVG 文件")
    p_fel.add_argument("--y", default=None, help="CV2 XVG 文件")
    p_fel.add_argument(
        "--xcol",
        type=int,
        default=1,
        help="CV1数据列索引；默认第二列",
    )
    p_fel.add_argument(
        "--ycol",
        type=int,
        default=1,
        help="CV2数据列索引；两个文件时默认第二列；单文件时按指定列读取",
    )
    p_fel.add_argument("--xlabel", default="RMSD (nm)")
    p_fel.add_argument("--ylabel", default="Radius of gyration (nm)")
    p_fel.add_argument("--title", default="")
    p_fel.add_argument("--prefix", default="fel")
    p_fel.add_argument("--bins", type=int, default=80)
    p_fel.add_argument("--levels", type=int, default=30)
    p_fel.add_argument("--temperature", type=float, default=300.0)
    p_fel.add_argument(
        "--pseudocount",
        type=float,
        default=1e-12,
        help="避免概率为0导致log无穷",
    )
    p_fel.add_argument(
        "--max-energy",
        type=float,
        default=None,
        help="绘图时截断自由能上限，例如20",
    )
    p_fel.add_argument("--cmap", default="viridis")
    p_fel.add_argument("--elev", type=float, default=35.0)
    p_fel.add_argument("--azim", type=float, default=-125.0)
    p_fel.add_argument("--surface-resolution", type=int, default=100)
    p_fel.set_defaults(func=plot_fel)

    return parser


def main():
    configure_style()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
