# FontForge Quickstart

A friendly guide for people who design, collect, or care about fonts.

## What this is

Think of FontForge as a batch-edit tool for your font collection, the way a photo library app lets you rename, resize, and convert a pile of pictures at once. It lives on your Mac at `~/fontforge/` and uses a small set of Python scripts to inspect, rename, convert, and fine-tune font files.

You work with it through a terminal. Each task is one short command. You never need to open a font editor.

**In this guide you will:**

- Check that your setup works.
- Run simple commands on real fonts.
- Learn how to prepare fonts for a website.
- See how Claude Code can run these tools for you.

---

## Getting started

You only need to do this once per terminal session.

**1. Open the Terminal app.**

**2. Go to the project folder:**

```bash
cd ~/fontforge
```

**3. Turn on the virtual environment.**

A virtual environment is a private sandbox of Python tools. It keeps FontForge's libraries separate from the rest of your Mac.

```bash
source venv/bin/activate
```

Your prompt will now start with `(venv)`. That means you are inside the sandbox.

**4. Run a quick check to confirm things work:**

```bash
python scripts/metrics.py fonts/Burbank --compare
```

You should see a table of Burbank fonts with weights, glyph counts, and file sizes. If you do, you are ready.

**Summary:**

- `cd ~/fontforge` gets you into the project.
- `source venv/bin/activate` turns on the Python sandbox.
- A working command prints a nice table; a broken one prints an error.

---

## Common tasks

Every command below can be copied and pasted as-is. Replace `Burbank` with your own family folder name when you want.

### See what's inside a font

Every font file carries hidden details: its designer, its weight, the letters it supports, and more. The `metrics.py` script prints all of that for you.

**1. Look at one font file:**

```bash
python scripts/metrics.py fonts/Burbank/BurbankText-Bold.ttf
```

**2. Compare every weight in a family side by side:**

```bash
python scripts/metrics.py fonts/Burbank --compare
```

**What you will see:**

- Family name, style, and designer.
- The glyph count (total number of shapes in the font).
- Which languages and scripts it covers (Latin, Cyrillic, Greek, and so on).
- Key heights: ascender, descender, cap height, x-height.
- Whether it is a variable font (more on those below).

**Summary:**

- Point the script at one file for full detail.
- Point it at a folder with `--compare` for a family overview.
- Add `--json` if you want machine-readable output.

### Tidy up messy font filenames

Fonts often arrive with odd names like `(Bold) MyFont.ttf` or `myfont - bold.ttf`. The `rename.py` script reads the real name stored inside each font and renames the file to a clean `FamilyName-Weight.ext` pattern.

Always preview before you commit. Previewing shows the changes without touching your files.

**1. Preview the renames for a family:**

```bash
python scripts/rename.py fonts/Samsung
```

**2. If the preview looks right, apply it:**

```bash
python scripts/rename.py fonts/Samsung --apply
```

**3. If something looks off, add `--verbose` to see more detail:**

```bash
python scripts/rename.py fonts/Samsung --verbose
```

**Summary:**

- Run once with no flag to preview.
- Add `--apply` to actually rename.
- The script reads each font's internal name, so it usually guesses well.

### Make fonts ready for a website

Websites prefer a format called WOFF2. It's like a zip file made specifically for fonts. A good WOFF2 loads fast because it is small and already compressed.

Preparing a family for the web has four stages. Each stage is one command.

- **Baseline shift**: nudge the letters up or down so they sit where you want them.
- **Hinting**: add small instructions that help fonts look sharp on low-resolution screens (especially on Windows).
- **Subsetting**: keep only the letters you need, such as Latin. This shrinks the file.
- **WOFF2**: compress the final file for the web.

You can skip baseline shift and hinting if your font already looks good. But the order matters if you do them: shift, then hint, then subset, then convert.

**1. (Optional) Shift the baseline down by 40 units. A unit is a tiny internal measurement; 40 is a small nudge.**

```bash
python scripts/baseline.py fonts/Burbank/ --shift -40 -o fonts/Burbank/shifted
```

**2. (Optional) Auto-hint the shifted fonts with strong stems, which is best for web:**

```bash
python scripts/hint.py fonts/Burbank/shifted/ -o fonts/Burbank/hinted --strong
```

**3. Convert to WOFF2 and keep only Latin and extended-Latin letters:**

```bash
python scripts/build.py fonts/Burbank/hinted/ \
  --format woff2 --subset "latin+latin-ext" \
  --output-dir fonts/Burbank/web
```

That's it. Your `fonts/Burbank/web/` folder now holds small, hinted, web-ready files.

**Short on time? The bare minimum is:**

```bash
python scripts/build.py fonts/Burbank --format woff2 --subset latin
```

**Summary:**

- WOFF2 plus Latin-only subset is the standard for most websites.
- Hint before you compress; compressing first wastes the hinting work.
- Keep your originals. Always write output to a new folder.

### Shift how a font sits on the line

Some fonts feel too high or too low next to your UI text. The `baseline.py` script moves every letter up or down by a set amount and keeps the font's reported heights in sync.

Numbers in fonts are measured in *units per em*, usually 1000 or 2048 per em. A shift of 40 is a small, visible nudge. A shift of 100 is large.

**1. Preview by shifting one file down by 40 units:**

```bash
python scripts/baseline.py fonts/Burbank/BurbankText-Regular.ttf --shift -40
```

**2. Shift a whole family down and write the results to a new folder:**

```bash
python scripts/baseline.py fonts/Burbank/ --shift -40 -o fonts/Burbank/shifted
```

**3. Fix only the Windows bounding-box metric (no shift). This stops Windows from clipping descenders on some fonts:**

```bash
python scripts/baseline.py fonts/Burbank/ --fit-win-metrics
```

**Summary:**

- Negative numbers move letters down. Positive numbers move them up.
- The script adjusts three internal height settings at once so the font stays consistent.
- Always run shifting *before* hinting.

### Look at kerning pairs

Kerning is the tiny spacing tweak between two specific letters. "AV" often gets pulled closer together so the two shapes fit visually. A font can contain hundreds of these pairs, stored in a modern table called GPOS (Glyph Positioning) or an older table called `kern`.

The `kern.py` script can pull all of them out as a simple spreadsheet.

**1. Dump every kerning pair for one font to a CSV file:**

```bash
python scripts/kern.py fonts/Burbank/BurbankText-Regular.ttf --dump -o pairs.csv
```

**2. Open `pairs.csv` in any spreadsheet app.** Each row looks like `A,V,-50` — meaning the letter V should sit 50 units closer to A.

**3. After editing, apply your CSV back to the font:**

```bash
python scripts/kern.py fonts/Burbank/BurbankText-Regular.ttf --apply pairs.csv -o out.ttf
```

**4. To widen the spacing of all lowercase letters by 10 units:**

```bash
python scripts/kern.py fonts/Burbank/BurbankText-Regular.ttf --spacing "lc:+10"
```

**Summary:**

- `--dump` exports every pair to CSV, even the class-based ones.
- Edit the CSV in any spreadsheet and use `--apply` to push changes back.
- Use `--spacing` to widen or tighten whole groups at once.

### Explore a variable font

A variable font is one file that contains many styles. Instead of shipping Light, Regular, and Bold as three files, one variable font holds all three and every step in between. You pick the weight you want by moving a slider called an *axis*.

Common axes include weight (`wght`), width (`wdth`), and slant (`slnt`). Variable fonts can also include *named instances* — preset stops like "Bold" or "Condensed" that the designer set up for you.

**1. See what axes and named styles a variable font offers:**

```bash
python scripts/variable.py fonts/Anthropic/AnthropicSansVariable-TextLight.ttf --info
```

**2. Pull out one named style as a regular static TTF:**

```bash
python scripts/variable.py fonts/Anthropic/AnthropicSansVariable-TextLight.ttf --instance "Bold"
```

**3. Or pick exact axis values:**

```bash
python scripts/variable.py fonts/Anthropic/AnthropicSansVariable-TextLight.ttf --instance "wght=700,wdth=100"
```

**Summary:**

- `--info` shows the sliders and presets a font offers.
- `--instance` freezes one setting into a normal font file.
- Variable fonts are great for web use because one file covers many weights.

---

## Using fontforge with Claude Code

Claude Code is Anthropic's AI assistant in your terminal. It can run FontForge commands for you if you ask in plain English. It does this through something called MCP (Model Context Protocol).

MCP is a small piece of glue. It lets Claude Code talk to outside tools in a safe, structured way. FontForge ships with its own MCP server that exposes 11 font tools, such as listing families, reading metrics, renaming files, and converting formats.

**1. Turn it on by adding this to your project's `.mcp.json` file (create the file if it doesn't exist):**

```json
{
  "mcpServers": {
    "fontforge": {
      "command": "/Users/visualval/fontforge/venv/bin/python",
      "args": ["/Users/visualval/fontforge/mcp-server/server.py"],
      "env": {}
    }
  }
}
```

**2. Restart Claude Code. It will pick up the new server.**

**3. Now you can ask questions like:**

- "List all my font families."
- "What are the metrics for Burbank Bold?"
- "Convert every Burbank font to WOFF2 with a Latin subset."

Claude Code will pick the right tool and run it. You stay in control — it will ask before doing anything that changes files.

**Summary:**

- MCP lets Claude Code call FontForge tools by itself.
- One JSON file turns it on.
- You can then describe tasks in plain English.

---

## Next steps

You now know enough to manage a font library day to day. When you want more control — custom Unicode ranges, PPEM tuning, building variable fonts from static masters, deep OpenType feature work — see the full technical reference:

- `~/fontforge/docs/guides/user-manual.md`

Every script also supports `--help`. For example:

```bash
python scripts/build.py --help
```

That prints every flag the script understands. Between `--help` and the manual, you can reach every corner of the toolkit.
