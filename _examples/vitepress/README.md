# VitePress deployment example

Use this source example with [Lizard (lizard.build)](https://lizard.build). It has no Dockerfile or service command overrides.

## Build locally

Run these commands from this directory:

```sh
npm ci
npm run docs:build
```

Run commands from this directory, which contains `package.json`. VitePress builds Markdown in `docs/` into `docs/.vitepress/dist`. Check `/guide`, `/probe.txt`, and a missing path.

## Deploy a local copy

Download or copy this directory into a standalone local folder. Install the CLI with `npm install -g @lizard-build/cli`, then run `lizard login` and complete sign-in. Run these commands from that local folder:

```sh
lizard init --name vitepress-example
lizard add --service web
lizard up --service web --port 80
lizard ps --json
```

If you already have a project, use `lizard link --project YOUR_PROJECT` instead of `init`. If the service exists, skip `add`.

For a GitHub source workflow, put this directory at the root of your own repository and use the [GitHub deployment guide](https://lizard.build/docs/framework-guides#prepare-the-project). Do not run `up` on a GitHub-backed service: it switches that service to uploaded source.

See the [full vitepress guide](https://lizard.build/docs/framework-guides/vitepress) for configuration and limits. Dependencies use the versions tested with this example; review updates before adopting them in your app.
