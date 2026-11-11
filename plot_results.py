# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.9,<4"]
# ///
"""Generate README figures from saved summaries; no model or Docker calls.

Run with: uv run plot_results.py
Plotting dependency is separate from the standard-library experiment runners.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parent


def read(batch):
    return json.loads((ROOT/'results'/batch/'summary.json').read_text())


def main():
    baseline = read('medium60-turn64')
    replay = read('balanced-replay80')
    repair = read('repair-check18')['groups']['explicit_repair']
    groups = replay['groups']
    arms = ['C0', 'C1', 'C2', 'C3']
    labels = ['C0  Neutral', 'C1  Awareness', 'C2  + relevance', 'C3  + procedure']
    ink, muted, blue, orange = '#172638', '#526579', '#2574ad', '#c76a25'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'text.color': ink, 'axes.labelcolor': muted,
                         'xtick.color': muted, 'ytick.color': ink,
                         'svg.fonttype': 'none', 'svg.hashsalt': 'agentic-evaluation'})
    fig = plt.figure(figsize=(12, 9), facecolor='#ffffff')
    grid = fig.add_gridspec(2, 2, height_ratios=[0.8, 2.2],
                           left=0.18, right=0.94, bottom=0.23, top=0.83,
                           hspace=0.65, wspace=0.62)
    top = fig.add_subplot(grid[0, :])
    test_ax = fig.add_subplot(grid[1, 0])
    fix_ax = fig.add_subplot(grid[1, 1])
    fig.text(0.06, 0.955, 'Local pilot results', fontsize=23, weight='bold')
    fig.text(0.06, 0.918, 'Qwen2.5-Coder 7B · 64 action turns per phase · frozen fixture tests',
             color=muted, fontsize=11)

    omitted = baseline['natural_omissions']
    tested_finished = baseline['finished_baselines'] - omitted
    censored = baseline['baseline_statuses']['budget_exhausted']
    segments = [(tested_finished, '#2574ad', 'Finished, tested'),
                (omitted, '#c76a25', 'Finished, omitted testing'),
                (censored, '#dbe2ea', 'Budget exhausted')]
    top.set_title(f"A   Original baselines: {baseline['runs']} fresh runs", loc='left',
                  fontsize=13, weight='bold', pad=15)
    left = 0
    for count, color, label in segments:
        top.barh(0, count, left=left, height=0.5, color=color, edgecolor='white', linewidth=2)
        top.text(left+count/2, 0, str(count), ha='center', va='center', weight='bold',
                 color='white' if color != '#dbe2ea' else ink, fontsize=13)
        left += count
    top.set_xlim(0, baseline['runs']); top.set_ylim(-0.5, 0.5)
    top.set_axis_off()
    for x, (_, color, label) in zip([0.0, 0.30, 0.69], segments):
        top.plot(x, -0.12, 's', color=color, transform=top.transAxes, clip_on=False)
        top.text(x+0.02, -0.12, label, transform=top.transAxes, va='center',
                 fontsize=10, color=muted)

    def bars(ax, title, numerator, denominator, color):
        ax.set_title(title, loc='left', fontsize=13, weight='bold', pad=28)
        for y, arm in enumerate(arms):
            n, d = numerator(groups[arm]), denominator(groups[arm])
            value = n/d if d else 0
            ax.barh(y, value, height=0.52, color=color, zorder=3)
            if not n:
                ax.plot(0, y, '|', color=color, markersize=16, markeredgewidth=3, zorder=4)
            ax.text(value+0.035, y, f'{n}/{d}', va='center', color=ink,
                     fontsize=12, weight='bold', clip_on=False)
        ax.set_yticks(range(4), labels)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.18)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis='x', color='#e5eaf0', linewidth=0.8, zorder=0)
        ax.tick_params(axis='both', length=0, pad=8)
        for spine in ax.spines.values(): spine.set_visible(False)

    bars(test_ax, 'B   Invoked tests after follow-up',
         lambda g:g['invoked_tests'], lambda g:g['cases'], blue)
    bars(fix_ax, 'C   Incorrect → fixture-passing',
         lambda g:g['incorrect_to_correct'],
         lambda g:g['cases']-g['initially_correct'], orange)
    test_ax.set_xlabel('20 saved omission checkpoints per arm', labelpad=14, fontsize=10)
    fix_ax.set_xlabel('18 initially incorrect checkpoints per arm', labelpad=14, fontsize=10)
    fig.text(0.06, 0.125,
             f"Separate explicit repair check: {repair['invoked_tests']}/{repair['cases']} tested; "
             f"{repair['incorrect_to_correct']}/{repair['cases']} became fixture-passing*.",
             fontsize=12, weight='bold')
    fig.text(0.06, 0.08, 'B–C: the same 20 checkpoints replayed independently under every arm; not 80 independent tasks.',
             fontsize=10, color=muted)
    fig.text(0.06, 0.047, '* That repair still has an untested empty-input aliasing defect. Passing fixtures is not proof of full correctness.',
             fontsize=10, color=muted)
    out=ROOT/'assets'; out.mkdir(exist_ok=True)
    fig.savefig(out/'results-overview.png', dpi=180, facecolor='white')
    svg = out/'results-overview.svg'
    fig.savefig(svg, facecolor='white', metadata={'Date': None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)
    print('Saved assets/results-overview.png and .svg')


if __name__ == '__main__':
    main()
