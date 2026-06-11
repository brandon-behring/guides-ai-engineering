// @ts-check
/**
 * astro.config.mjs — guides-ai-engineering.
 *
 * The AI-native dimensions of AI engineering, as a multi-guide repo (guides as
 * content collections). Deploys to guides.brandon-behring.dev/ai-engineering/
 * via subroute proxy from the hub repo. `base: '/ai-engineering/'` aligns
 * Astro's link generation with the deployed URL prefix.
 *
 * Uses the `styles: [researchPortfolioStyle, guidesFamilyStyle]` composition
 * (book-scaffold-astro v4.0.0+). guidesFamilyStyle is inline-duplicated below
 * (canonical source: ~/guides/shared/styles/guides-family.ts).
 */
import {
  defineBookConfig,
  researchPortfolioStyle,
  defineStyle,
} from '@brandon_m_behring/book-scaffold-astro';

const guidesFamilyStyle = defineStyle({
  name: 'guides-family',
  site: 'https://guides.brandon-behring.dev',
  routes: { frontmatter: { enabled: true, prefix: '' } },
  deploy: 'workers',
});

export default await defineBookConfig({
  styles: [researchPortfolioStyle, guidesFamilyStyle],
  base: '/ai-engineering/',
  // The custom two-guide landing (src/pages/index.astro) replaces the
  // scaffold's auto-injected `/`; suppress the injection so the routes
  // don't collide (scaffold #129 escape hatch).
  routes: { landing: false },
});
