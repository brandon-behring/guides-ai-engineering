#!/usr/bin/env node
/**
 * add-chapter-numbering.mjs — one-shot, idempotent.
 *
 * Adds `part` (per-guide) and `chapter` (from the NN filename prefix) to the
 * YAML frontmatter of every NN-*.mdx chapter in the four guide folders.
 *
 * Safety contract:
 *  - Only the four guide folders are touched (frontmatter/ is excluded).
 *  - Keys are inserted immediately after the `slug:` line, or after `title:`
 *    if no slug exists. They are only added when ABSENT (idempotent).
 *  - The file body and every other frontmatter field are preserved exactly:
 *    we splice into the array of original lines and re-join with the file's
 *    own newline style, never re-serializing YAML.
 *  - A file is rewritten only if it actually changed.
 *
 * Usage:  node scripts/add-chapter-numbering.mjs [--check]
 *   --check : report what would change, write nothing, exit 1 if changes pending.
 */
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, '..');
const CONTENT = path.join(REPO, 'src', 'content');

// Guide folder -> part number. Order is the canonical book order.
const PART_BY_GUIDE = {
  evaluation: 1,
  'llm-app-engineering': 2,
  'production-ai-systems': 3,
  'working-with-ai': 4,
};

const CHECK = process.argv.includes('--check');

// NN- prefix, where NN is one or two digits. Captures the integer.
const NN_PREFIX = /^(\d{1,2})-.+\.mdx$/;

/** Split content into [eol, lines[]] preserving the dominant newline. */
function splitLines(text) {
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  // Keep a trailing-newline sentinel so re-join is byte-exact.
  return [eol, text.split(eol)];
}

/** Find the [start, end] line indices of the YAML frontmatter fence pair. */
function frontmatterBounds(lines) {
  if (lines[0].trim() !== '---') return null;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === '---') return [0, i];
  }
  return null;
}

async function main() {
  const results = [];
  const guides = Object.keys(PART_BY_GUIDE);

  for (const guide of guides) {
    const dir = path.join(CONTENT, guide);
    let entries;
    try {
      entries = await fs.readdir(dir);
    } catch (e) {
      throw new Error(`Guide folder missing: ${dir}`);
    }
    const part = PART_BY_GUIDE[guide];

    const mdx = entries.filter((f) => f.endsWith('.mdx')).sort();
    for (const file of mdx) {
      const m = file.match(NN_PREFIX);
      if (!m) {
        results.push({ file: path.join(guide, file), action: 'SKIP-no-NN-prefix' });
        continue;
      }
      const chapter = parseInt(m[1], 10);
      const abs = path.join(dir, file);
      const raw = await fs.readFile(abs, 'utf8');
      const [eol, lines] = splitLines(raw);
      const bounds = frontmatterBounds(lines);
      if (!bounds) throw new Error(`No frontmatter fence in ${abs}`);
      const [fmStart, fmEnd] = bounds; // fmEnd = closing '---' index

      // Idempotency: scan only the frontmatter region for existing keys.
      let hasPart = false;
      let hasChapter = false;
      let slugIdx = -1;
      let titleIdx = -1;
      for (let i = fmStart + 1; i < fmEnd; i++) {
        const line = lines[i];
        if (/^part:\s/.test(line)) hasPart = true;
        if (/^chapter:\s/.test(line)) hasChapter = true;
        if (slugIdx === -1 && /^slug:\s/.test(line)) slugIdx = i;
        if (titleIdx === -1 && /^title:\s/.test(line)) titleIdx = i;
      }

      if (hasPart && hasChapter) {
        results.push({ file: path.join(guide, file), action: 'already-present', part, chapter });
        continue;
      }

      const insertAfter = slugIdx !== -1 ? slugIdx : titleIdx;
      if (insertAfter === -1) {
        throw new Error(`No slug: or title: line in frontmatter of ${abs}`);
      }

      // Build only the missing keys, preserving any one that already exists.
      const toInsert = [];
      if (!hasPart) toInsert.push(`part: ${part}`);
      if (!hasChapter) toInsert.push(`chapter: ${chapter}`);

      const newLines = [
        ...lines.slice(0, insertAfter + 1),
        ...toInsert,
        ...lines.slice(insertAfter + 1),
      ];
      const out = newLines.join(eol);

      if (out === raw) {
        results.push({ file: path.join(guide, file), action: 'no-change', part, chapter });
        continue;
      }

      if (!CHECK) await fs.writeFile(abs, out, 'utf8');
      results.push({
        file: path.join(guide, file),
        action: CHECK ? 'WOULD-WRITE' : 'wrote',
        part,
        chapter,
        inserted: toInsert.join(' | '),
        anchor: slugIdx !== -1 ? 'after slug' : 'after title',
      });
    }
  }

  // Report.
  const wrote = results.filter((r) => r.action === 'wrote' || r.action === 'WOULD-WRITE');
  const skipped = results.filter((r) => r.action.startsWith('SKIP'));
  for (const r of results) {
    console.log(
      `${r.action.padEnd(16)} part=${r.part ?? '-'} chapter=${String(r.chapter ?? '-').padStart(2)}  ${r.file}` +
        (r.inserted ? `   [${r.inserted}; ${r.anchor}]` : ''),
    );
  }
  console.log('---');
  console.log(`total=${results.length}  changed=${wrote.length}  skipped=${skipped.length}`);
  if (skipped.length) {
    console.log('SKIPPED (no NN prefix — review these):');
    for (const r of skipped) console.log(`  ${r.file}`);
  }
  if (CHECK && wrote.length) process.exitCode = 1;
}

main().catch((e) => {
  console.error(e);
  process.exit(2);
});
