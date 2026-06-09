/**
 * src/content.config.ts — guides-ai-engineering content collections.
 *
 * Multi-guide repo: each guide is a content collection under src/content/<guide>/.
 * Evaluation is the first guide. Adding a guide = add a collection here + its
 * content dir + a route (see src/pages/). The chapter schema extends the
 * scaffold's `researchPortfolioChapterSchema` with the v0.2 pedagogical-metadata
 * fields (mode/target/ordering/los/load_targets/paradigms/...), carried over
 * from the guides-experimentation pilot.
 *
 * NOTE (multi-guide routing): one `chapters` collection over ./src/content, so every
 * guide's chapters (src/content/<guide>/*.mdx) share it. A `generateId` (below) namespaces
 * each id by its guide folder, so the scaffold route serves /chapters/<guide>/<slug>/ and
 * slugs only need to be unique *within* a guide. (Without it, Astro's glob keys ids off the
 * frontmatter `slug` and routes flat at /chapters/<slug>/, forcing globally-unique slugs.)
 * The `!frontmatter/**` guard keeps the frontmatter collection out of `chapters`. The shared
 * /chapters/ index still lists all guides mixed; a per-guide index/landing waits on scaffold
 * #15 (multibook, deferred post-v4.x).
 */
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { researchPortfolioChapterSchema } from '@brandon_m_behring/book-scaffold-astro';
import { frontmatterCollection } from '@brandon_m_behring/book-scaffold-astro/schemas';

/** v0.2 chapter-metadata extensions (per guides design doc; see hub). */
const v02ChapterExtensions = z.object({
  mode: z.enum(['tutorial', 'how-to', 'reference', 'explanation']).optional(),
  target: z.enum(['retention', 'transfer', 'both']).optional(),
  ordering: z
    .enum(['concept-first', 'problem-first', 'construction-first'])
    .optional(),
  research_debt_addressed: z.string().optional(),
  commitment: z.enum(['long-lived', 'frozen', 'career-stage']).optional(),
  paradigms: z
    .array(z.enum(['default', 'udl', 'srl', 'andragogy']))
    .optional()
    .default(['default']),
  task_classes: z.array(z.string()).optional(),
  companion_modules: z.array(z.string()).optional(),
  los: z
    .array(
      z.object({
        id: z.string(),
        bloom: z.enum([
          'define',
          'explain',
          'calculate',
          'compare',
          'analyze',
          'design',
        ]),
        statement: z.string(),
        anchor: z.string(),
        threshold: z.boolean().optional().default(false),
      })
    )
    .optional(),
  load_targets: z
    .object({
      intrinsic: z.enum(['low', 'medium', 'high']).optional(),
      extraneous: z.enum(['low', 'medium', 'high']).optional(),
      germane: z.enum(['low', 'medium', 'high']).optional(),
    })
    .optional(),
});

const chapters = defineCollection({
  loader: glob({
    pattern: ['**/*.{md,mdx}', '!**/_*', '!frontmatter/**'],
    base: './src/content',
    // Namespace each chapter's id (hence its URL) by its guide folder so guides can
    // share slugs: id -> "<guide>/<slug>", served at /chapters/<guide>/<slug>/. Astro's
    // glob keys ids off frontmatter `slug` by default (which would be flat, /chapters/<slug>/,
    // forcing globally-unique slugs); this restores the per-guide URL prefix with no custom
    // route. `entry` is the file path relative to base, e.g. "evaluation/00-why-evaluation.mdx".
    generateId: ({ entry, data }) => {
      const guide = entry.split('/')[0];
      const slug = (data && data.slug) || entry.replace(/\.[^.]+$/, '').split('/').pop();
      return `${guide}/${slug}`;
    },
  }),
  schema: researchPortfolioChapterSchema.merge(v02ChapterExtensions),
});

const frontmatter = frontmatterCollection(
  z.object({
    slug: z.string(),
    title: z.string(),
    order: z.number(),
    description: z.string().optional(),
  })
);

export const collections = { chapters, frontmatter };
