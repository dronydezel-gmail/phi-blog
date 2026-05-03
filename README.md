# phi · essays

Personal blog. Astro static site. Content lives in `src/content/posts/` as
markdown with YAML frontmatter; everything renders to a static site under
`dist/`.

## Develop

```sh
npm install
npm run dev          # http://localhost:4321
```

## Build

```sh
npm run build        # → dist/
npm run preview
```

## Deploy to Vercel

Astro auto-detects on Vercel. Two paths:

**Via the dashboard (recommended for first deploy):** push this repo to
GitHub, then "Add new project" on vercel.com and pick the repo. Framework
preset = Astro, build command = `npm run build`, output = `dist`. Vercel
fills these in automatically.

**Via CLI:**

```sh
npm i -g vercel
vercel              # first run links the project
vercel --prod       # production deploy
```

After the first deploy, set the production domain to your liking and
update `site:` in `astro.config.mjs` so canonical URLs and OG image paths
are correct.

## Add a post

1. Create `src/content/posts/<slug>.md`
2. Add frontmatter (see existing posts; `title`, `pubDate`, `description`
   are required; `subtitle`, `cover`, `audio`, `pdf`, `tags` optional).
3. Write the body in markdown. Drop images into `public/images/` and
   reference them as `/images/foo.png`.
4. `npm run dev` to preview.
