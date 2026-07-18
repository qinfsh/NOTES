#!/usr/bin/env python3
"""
GROMACS 分析可视化脚本

支持：
1. RMSD
2. RMSF
3. 回旋半径 Rg
4. 自由能景观 FEL（二维等高线 + 三维形貌图）

主要特性：
- 自动读取 XVG 中的标题、X/Y 轴标签和单位
- 不擅自进行 ps/ns 数值转换
- 可通过 --xlabel、--ylabel、--title 手动覆盖 XVG 元数据
- 自动忽略 XVG 中的 #、@ 注释行和 & 数据集分隔符
- 支持 RMSD、RMSF、Rg 平滑
- FEL 支持单文件双变量或两个独立 XVG 文件
- 输出二维 FEL、三维 FEL 及网格数据

依赖：
    numpy
    matplotlib

示例：
    python gmx_analysis_plot.py rmsd -f rmsd.xvg -o rmsd.png
    python gmx_analysis_plot.py rmsf -f rmsf.xvg -o rmsf.png
    python gmx_analysis_plot.py rg -f gyrate.xvg -o rg.png

两个独立文件计算 FEL：
    python gmx_analysis_plot.py fel \
        --x rmsd.xvg \
        --y gyrate.xvg \
        --prefix fel

同一文件中包含时间、CV1、CV2：
    python gmx_analysis_plot.py fel \
        -f cv_data.xvg \
        --xcol 1 \
        --ycol 2 \
        --prefix fel
"""

import argparse
from pathlib import Path
import re
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def clean_xvg_label(label):
    """
    清理 XVG/Grace 标签中的常见格式控制符。

    说明：
    Grace 使用 \\s、\\N 等标记上下标。
    这里进行基础清理，使标签适合 Matplotlib 显示。
    """
    if not label:
        return None

    replacements = {
        r"\N": "",
        r"\S": "",
        r"\s": "",
        r"\f{}": "",
    }

    for old, new in replacements.items():
        label = label.replace(old, new)

    label = re.sub(r"\f\{[^}]*\}", "", label)
    return label.strip()


def extract_quoted_text(line):
    """提取 XVG 元数据行中双引号内的文字。"""
    match = re.search(r'"(.*)"', line)
    if match:
        return clean_xvg_label(match.group(1))
    return None


def read_xvg(path):
    """
    读取 GROMACS XVG 文件，同时提取元数据。

    返回
    ----
    data : numpy.ndarray
        XVG 中的数值数据。

    metadata : dict
        可包含：
        - title
        - subtitle
        - xlabel
        - ylabel
        - legends
        - source
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")

    rows = []
    metadata = {
        "title": None,
        "subtitle": None,
        "xlabel": None,
        "ylabel": None,
        "legends": {},
        "source": str(path),
    }

    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for raw_line in fh:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("@"):
                if re.match(
                    r"^@\s+title\s+",
                    line,
                    flags=re.IGNORECASE,
                ):
                    metadata["title"] = extract_quoted_text(line)

                elif re.match(
                    r"^@\s+subtitle\s+",
                    line,
                    flags=re.IGNORECASE,
                ):
                    metadata["subtitle"] = extract_quoted_text(line)

                elif re.match(
                    r"^@\s+xaxis\s+label\s+",
                    line,
                    flags=re.IGNORECASE,
                ):
                    metadata["xlabel"] = extract_quoted_text(line)

                elif re.match(
                    r"^@\s+yaxis\s+label\s+",
                    line,
                    flags=re.IGNORECASE,
                ):
                    metadata["ylabel"] = extract_quoted_text(line)

                else:
                    legend_match = re.match(
                        r'^@\s+s(\d+)\s+legend\s+"(.*)"',
                        line,
                        flags=re.IGNORECASE,
                    )
                    if legend_match:
                        series_index = int(legend_match.group(1))
                        legend_text = clean_xvg_label(
                            legend_match.group(2)
                        )
                        metadata["legends"][series_index] = legend_text

                continue

            if line.startswith(("#", "&")):
                continue

            try:
                values = [float(v) for v in line.split()]
            except ValueError:
                continue

            rows.append(values)

    if not rows:
        raise ValueError(f"{path} 中没有可读取的数值数据。")

    column_counts = {len(row) for row in rows}
    if len(column_counts) != 1:
        raise ValueError(
            f"{path} 中的数据列数不一致：{sorted(column_counts)}。"
        )

    data = np.asarray(rows, dtype=float)

    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"{path} 至少应包含两列数值。")

    return data, metadata


def configure_style():
    """配置统一的论文绘图风格。"""
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
    """计算保持原长度的移动平均。"""
    if window <= 1:
        return y.copy()

    if window > len(y):
        raise ValueError("平滑窗口大于数据点总数。")

    kernel = np.ones(window, dtype=float) / window
    return np.convolve(y, kernel, mode="same")


def validate_column(data, column, name):
    """检查列索引是否合法。"""
    if column < 0 or column >= data.shape[1]:
        raise ValueError(
            f"指定的 {name} 列索引 {column} 超出范围；"
            f"文件只有 {data.shape[1]} 列，合法索引为 "
            f"0 至 {data.shape[1] - 1}。"
        )


def choose_label(user_label, metadata_label, fallback):
    """用户标签优先，其次 XVG 标签，最后使用默认标签。"""
    if user_label:
        return user_label
    if metadata_label:
        return metadata_label
    return fallback


def plot_series(args, default_ylabel, default_color, default_title):
    """绘制 RMSD、RMSF 或回旋半径等一维曲线。"""
    data, metadata = read_xvg(args.file)

    validate_column(data, args.xcol, "X")
    validate_column(data, args.ycol, "Y")

    x = data[:, args.xcol]
    y = data[:, args.ycol]

    valid_mask = np.isfinite(x) & np.isfinite(y)
    x = x[valid_mask]
    y = y[valid_mask]

    if len(x) == 0:
        raise ValueError("删除 NaN 和无穷值后，没有可绘制的数据。")

    if args.smooth > 1:
        y = moving_average(y, args.smooth)

    fig, ax = plt.subplots(figsize=(args.width, args.height))

    ax.plot(
        x,
        y,
        color=args.color or default_color,
        linewidth=args.linewidth,
        label=args.legend if args.legend else None,
    )

    xlabel = choose_label(
        args.xlabel,
        metadata.get("xlabel"),
        "X",
    )
    ylabel = choose_label(
        args.ylabel,
        metadata.get("ylabel"),
        default_ylabel,
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if args.title:
        ax.set_title(args.title)
    elif args.show_xvg_title and metadata.get("title"):
        ax.set_title(metadata["title"])
    elif args.show_default_title:
        ax.set_title(default_title)

    xmin = float(np.nanmin(x))
    xmax = float(np.nanmax(x))

    if xmin == xmax:
        padding = abs(xmin) * 0.05 if xmin != 0 else 1.0
        ax.set_xlim(xmin - padding, xmax + padding)
    else:
        ax.set_xlim(xmin, xmax)

    if args.xmin is not None or args.xmax is not None:
        current_left, current_right = ax.get_xlim()
        ax.set_xlim(
            args.xmin if args.xmin is not None else current_left,
            args.xmax if args.xmax is not None else current_right,
        )

    if args.ymin is not None or args.ymax is not None:
        current_bottom, current_top = ax.get_ylim()
        ax.set_ylim(
            args.ymin if args.ymin is not None else current_bottom,
            args.ymax if args.ymax is not None else current_top,
        )

    if args.mean_line:
        mean_value = float(np.nanmean(y))
        ax.axhline(
            mean_value,
            linestyle="--",
            linewidth=1.0,
            color="black",
            alpha=0.75,
            label=f"Mean = {mean_value:.4g}",
        )

    if args.grid:
        ax.grid(
            True,
            linestyle="--",
            linewidth=0.5,
            alpha=0.35,
        )

    if args.legend or args.mean_line:
        ax.legend()

    ax.tick_params(direction="in")
    fig.tight_layout()
    fig.savefig(
        args.output,
        bbox_inches="tight",
        transparent=args.transparent,
    )
    plt.close(fig)

    print(f"输入文件：{Path(args.file).resolve()}")
    print(f"读取到的 X 轴标签：{metadata.get('xlabel')}")
    print(f"读取到的 Y 轴标签：{metadata.get('ylabel')}")
    print(f"最终使用的 X 轴标签：{xlabel}")
    print(f"最终使用的 Y 轴标签：{ylabel}")
    print(f"已生成：{Path(args.output).resolve()}")


def align_by_time(data_x, data_y, x_value_col, y_value_col):
    """
    按最短长度对齐两个轨迹。

    注意：
    这里按数据点顺序配对，不根据时间值插值。
    若两个轨迹采样频率不同，应先进行统一采样。
    """
    validate_column(data_x, x_value_col, "CV1")
    validate_column(data_y, y_value_col, "CV2")

    x = data_x[:, x_value_col]
    y = data_y[:, y_value_col]

    n = min(len(x), len(y))

    if len(x) != len(y):
        print(
            f"警告：两个输入长度不同，将按前 {n} 个点配对。",
            file=sys.stderr,
        )

    return x[:n], y[:n]


def compute_fel(x, y, bins, temperature, pseudocount):
    """
    计算二维自由能景观。

    G = -k_B T ln(P / Pmax)

    自由能单位：kJ/mol
    """
    hist, x_edges, y_edges = np.histogram2d(
        x,
        y,
        bins=bins,
    )
    hist = hist.T

    if pseudocount < 0:
        raise ValueError("pseudocount 不能为负数。")

    prob = hist.astype(float)

    if pseudocount > 0:
        prob = prob + pseudocount

    total = np.sum(prob)
    if total <= 0:
        raise ValueError("概率分布总和为 0，无法计算自由能。")

    prob = prob / total

    positive_mask = prob > 0
    if not np.any(positive_mask):
        raise ValueError("没有非零概率区域，无法计算自由能。")

    prob_max = np.max(prob[positive_mask])
    k_b = 0.008314462618  # kJ mol^-1 K^-1

    free_energy = np.full_like(prob, np.nan, dtype=float)
    free_energy[positive_mask] = (
        -k_b
        * temperature
        * np.log(prob[positive_mask] / prob_max)
    )

    x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    X, Y = np.meshgrid(x_centers, y_centers)

    return X, Y, free_energy, hist


def subset_by_index(x, y, start_index, end_index):
    """按数据点索引截取 FEL 输入。"""
    n = len(x)

    start = start_index if start_index is not None else 0
    end = end_index if end_index is not None else n

    if start < 0:
        start = max(0, n + start)

    if end < 0:
        end = max(0, n + end)

    if start >= end:
        raise ValueError(
            f"无效的数据截取范围：start-index={start_index}, "
            f"end-index={end_index}。"
        )

    return x[start:end], y[start:end]


def plot_fel(args):
    """绘制二维和三维自由能景观。"""
    x_metadata = {}
    y_metadata = {}

    if args.file:
        data, metadata = read_xvg(args.file)

        validate_column(data, args.xcol, "CV1")
        validate_column(data, args.ycol, "CV2")

        x = data[:, args.xcol]
        y = data[:, args.ycol]

        x_metadata = metadata
        y_metadata = metadata

    else:
        if not args.x or not args.y:
            raise ValueError(
                "FEL 必须提供 -f，或同时提供 --x 和 --y。"
            )

        data_x, x_metadata = read_xvg(args.x)
        data_y, y_metadata = read_xvg(args.y)

        x, y = align_by_time(
            data_x,
            data_y,
            args.xcol,
            args.ycol,
        )

    valid_mask = np.isfinite(x) & np.isfinite(y)
    x = x[valid_mask]
    y = y[valid_mask]

    x, y = subset_by_index(
        x,
        y,
        args.start_index,
        args.end_index,
    )

    if len(x) < 10:
        raise ValueError("有效数据点少于 10 个，无法计算自由能景观。")

    X, Y, G, hist = compute_fel(
        x=x,
        y=y,
        bins=args.bins,
        temperature=args.temperature,
        pseudocount=args.pseudocount,
    )

    if args.max_energy is not None:
        G_plot = np.where(
            np.isfinite(G),
            np.minimum(G, args.max_energy),
            np.nan,
        )
    else:
        G_plot = G.copy()

    finite_values = G_plot[np.isfinite(G_plot)]
    if finite_values.size == 0:
        raise ValueError("自由能网格中没有有限数值。")

    energy_min = float(np.min(finite_values))
    energy_max = float(np.max(finite_values))

    if np.isclose(energy_min, energy_max):
        energy_max = energy_min + 1e-6

    levels = np.linspace(
        energy_min,
        energy_max,
        args.levels,
    )

    xlabel = choose_label(
        args.xlabel,
        x_metadata.get("ylabel") if not args.file else None,
        "CV1",
    )
    ylabel = choose_label(
        args.ylabel,
        y_metadata.get("ylabel") if not args.file else None,
        "CV2",
    )

    # 单文件通常无法从一个 yaxis 标签区分 CV1 和 CV2，
    # 因此单文件模式下默认使用 CV1/CV2，除非用户手动指定。
    if args.file:
        xlabel = args.xlabel or "CV1"
        ylabel = args.ylabel or "CV2"

    prefix = Path(args.prefix)
    contour_path = prefix.with_name(prefix.name + "_2D.png")
    surface_path = prefix.with_name(prefix.name + "_3D.png")
    data_path = prefix.with_name(prefix.name + "_grid.dat")

    # 二维等高线图
    fig, ax = plt.subplots(figsize=(args.width_2d, args.height_2d))

    masked_G = np.ma.masked_invalid(G_plot)

    contour = ax.contourf(
        X,
        Y,
        masked_G,
        levels=levels,
        cmap=args.cmap,
    )

    line_step = max(1, len(levels) // 10)
    ax.contour(
        X,
        Y,
        masked_G,
        levels=levels[::line_step],
        linewidths=0.35,
        colors="k",
        alpha=0.35,
    )

    cbar = fig.colorbar(contour, ax=ax, pad=0.03)
    cbar.set_label("Free energy (kJ/mol)")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if args.title:
        ax.set_title(args.title)

    if args.grid:
        ax.grid(
            True,
            linestyle="--",
            linewidth=0.5,
            alpha=0.25,
        )

    ax.tick_params(direction="in")
    fig.tight_layout()
    fig.savefig(
        contour_path,
        bbox_inches="tight",
        transparent=args.transparent,
    )
    plt.close(fig)

    # 三维自由能形貌图
    fig = plt.figure(figsize=(args.width_3d, args.height_3d))
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(
        X,
        Y,
        masked_G,
        cmap=args.cmap,
        linewidth=0,
        antialiased=True,
        rcount=min(args.surface_resolution, G_plot.shape[0]),
        ccount=min(args.surface_resolution, G_plot.shape[1]),
    )

    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.set_zlabel("Free energy (kJ/mol)", labelpad=8)

    if args.title:
        ax.set_title(args.title)

    ax.view_init(
        elev=args.elev,
        azim=args.azim,
    )

    fig.colorbar(
        surf,
        ax=ax,
        shrink=0.65,
        pad=0.12,
        label="Free energy (kJ/mol)",
    )

    fig.tight_layout()
    fig.savefig(
        surface_path,
        bbox_inches="tight",
        transparent=args.transparent,
    )
    plt.close(fig)

    flat = np.column_stack((
        X.ravel(),
        Y.ravel(),
        G.ravel(),
        hist.ravel(),
    ))

    np.savetxt(
        data_path,
        flat,
        header="CV1 CV2 FreeEnergy_kJ_per_mol Count",
        fmt="%.8f",
    )

    print(f"FEL 使用的数据点数：{len(x)}")
    print(f"CV1 标签：{xlabel}")
    print(f"CV2 标签：{ylabel}")
    print(f"已生成二维自由能图：{contour_path.resolve()}")
    print(f"已生成三维形貌图：{surface_path.resolve()}")
    print(f"已保存自由能网格：{data_path.resolve()}")


def add_common_series_args(parser):
    """添加 RMSD、RMSF、Rg 共用参数。"""
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="输入 XVG 文件",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="输出图片文件，如 png、pdf、svg 或 tiff",
    )
    parser.add_argument(
        "--xcol",
        type=int,
        default=0,
        help="X 数据列索引，默认 0",
    )
    parser.add_argument(
        "--ycol",
        type=int,
        default=1,
        help="Y 数据列索引，默认 1",
    )
    parser.add_argument(
        "--xlabel",
        default=None,
        help="自定义 X 轴标签；不设置时读取 XVG",
    )
    parser.add_argument(
        "--ylabel",
        default=None,
        help="自定义 Y 轴标签；不设置时读取 XVG",
    )
    parser.add_argument(
        "--title",
        default="",
        help="自定义标题",
    )
    parser.add_argument(
        "--show-xvg-title",
        action="store_true",
        help="未设置 --title 时显示 XVG 中的标题",
    )
    parser.add_argument(
        "--show-default-title",
        action="store_true",
        help="XVG 无标题时显示程序默认标题",
    )
    parser.add_argument(
        "--legend",
        default=None,
        help="曲线图例文字",
    )
    parser.add_argument(
        "--color",
        default=None,
        help="曲线颜色，如 '#B22222' 或 red",
    )
    parser.add_argument(
        "--linewidth",
        type=float,
        default=1.2,
        help="曲线宽度，默认 1.2",
    )
    parser.add_argument(
        "--smooth",
        type=int,
        default=1,
        help="移动平均窗口，默认不平滑",
    )
    parser.add_argument(
        "--mean-line",
        action="store_true",
        help="显示平均值虚线",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="显示辅助网格",
    )
    parser.add_argument("--xmin", type=float, default=None)
    parser.add_argument("--xmax", type=float, default=None)
    parser.add_argument("--ymin", type=float, default=None)
    parser.add_argument("--ymax", type=float, default=None)
    parser.add_argument("--width", type=float, default=4.5)
    parser.add_argument("--height", type=float, default=3.5)
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="保存透明背景",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "GROMACS RMSD、RMSF、Rg 与自由能景观可视化工具；"
            "自动读取 XVG 坐标标签和单位"
        )
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    p_rmsd = sub.add_parser(
        "rmsd",
        help="绘制 RMSD",
    )
    add_common_series_args(p_rmsd)
    p_rmsd.set_defaults(
        func=lambda a: plot_series(
            a,
            default_ylabel="RMSD",
            default_color="#B22222",
            default_title="RMSD",
        )
    )

    p_rmsf = sub.add_parser(
        "rmsf",
        help="绘制 RMSF",
    )
    add_common_series_args(p_rmsf)
    p_rmsf.set_defaults(
        func=lambda a: plot_series(
            a,
            default_ylabel="RMSF",
            default_color="#1F77B4",
            default_title="RMSF",
        )
    )

    p_rg = sub.add_parser(
        "rg",
        help="绘制回旋半径",
    )
    add_common_series_args(p_rg)
    p_rg.set_defaults(
        func=lambda a: plot_series(
            a,
            default_ylabel="Radius of gyration",
            default_color="#2E8B57",
            default_title="Radius of Gyration",
        )
    )

    p_fel = sub.add_parser(
        "fel",
        help="绘制二维和三维自由能景观",
    )

    p_fel.add_argument(
        "-f",
        "--file",
        default=None,
        help="包含 CV1 和 CV2 的同一个文件",
    )
    p_fel.add_argument(
        "--x",
        default=None,
        help="CV1 XVG 文件",
    )
    p_fel.add_argument(
        "--y",
        default=None,
        help="CV2 XVG 文件",
    )
    p_fel.add_argument(
        "--xcol",
        type=int,
        default=1,
        help="CV1 数据列索引，默认 1",
    )
    p_fel.add_argument(
        "--ycol",
        type=int,
        default=1,
        help="CV2 数据列索引；双文件默认 1",
    )
    p_fel.add_argument(
        "--xlabel",
        default=None,
        help="CV1 标签；双文件模式默认读取第一个 XVG 的 Y 轴标签",
    )
    p_fel.add_argument(
        "--ylabel",
        default=None,
        help="CV2 标签；双文件模式默认读取第二个 XVG 的 Y 轴标签",
    )
    p_fel.add_argument(
        "--title",
        default="",
    )
    p_fel.add_argument(
        "--prefix",
        default="fel",
    )
    p_fel.add_argument(
        "--bins",
        type=int,
        default=80,
    )
    p_fel.add_argument(
        "--levels",
        type=int,
        default=30,
    )
    p_fel.add_argument(
        "--temperature",
        type=float,
        default=300.0,
    )
    p_fel.add_argument(
        "--pseudocount",
        type=float,
        default=0.0,
        help=(
            "直方图伪计数；默认 0，空网格显示为空白。"
            "若需要填充空网格，可设置如 1e-12"
        ),
    )
    p_fel.add_argument(
        "--max-energy",
        type=float,
        default=25.0,
        help="绘图自由能上限，默认 25 kJ/mol；设置负值无意义",
    )
    p_fel.add_argument(
        "--cmap",
        default="viridis",
    )
    p_fel.add_argument(
        "--elev",
        type=float,
        default=35.0,
    )
    p_fel.add_argument(
        "--azim",
        type=float,
        default=-125.0,
    )
    p_fel.add_argument(
        "--surface-resolution",
        type=int,
        default=100,
    )
    p_fel.add_argument(
        "--start-index",
        type=int,
        default=None,
        help="从指定数据点索引开始计算 FEL",
    )
    p_fel.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="计算 FEL 的结束索引，不包含该点",
    )
    p_fel.add_argument(
        "--grid",
        action="store_true",
    )
    p_fel.add_argument(
        "--transparent",
        action="store_true",
    )
    p_fel.add_argument(
        "--width-2d",
        type=float,
        default=5.2,
    )
    p_fel.add_argument(
        "--height-2d",
        type=float,
        default=4.2,
    )
    p_fel.add_argument(
        "--width-3d",
        type=float,
        default=6.2,
    )
    p_fel.add_argument(
        "--height-3d",
        type=float,
        default=5.0,
    )

    p_fel.set_defaults(func=plot_fel)

    return parser


def main():
    configure_style()
    parser = build_parser()
    args = parser.parse_args()

    try:
        if (
            args.command == "fel"
            and args.max_energy is not None
            and args.max_energy <= 0
        ):
            raise ValueError("--max-energy 必须大于 0。")

        args.func(args)

    except (
        FileNotFoundError,
        ValueError,
        IndexError,
        OSError,
    ) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

