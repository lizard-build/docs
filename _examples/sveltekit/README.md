# SvelteKit deployment example

Use this source example with [Lizard (lizard.build)](https://lizard.build). It has no Dockerfile or service command overrides.

## Build locally

Run these commands from this directory:

```sh
npm ci
npm run build
```

This example explicitly uses `@sveltejs/adapter-node`. After deployment, set `ORIGIN` to the exact public HTTPS origin with `lizard secrets set ORIGIN=https://YOUR_PUBLIC_HOST --service web`. Check `/guide`, `/api/probe`, `/action`, and a missing path. Submit the form on `/action`; it should display the submitted value. The example keeps no submitted data.

## Deploy a local copy

Download or copy this directory into a standalone local folder. Install the CLI with `npm install -g @lizard-build/cli`, then run `lizard login` and complete sign-in. Run these commands from that local folder:

```sh
lizard init --name sveltekit-example
lizard add --service web
lizard up --service web --port 3000
lizard ps --json
```

If you already have a project, use `lizard link --project YOUR_PROJECT` instead of `init`. If the service exists, skip `add`.

For a GitHub source workflow, put this directory at the root of your own repository and use the [GitHub deployment guide](https://lizard.build/docs/framework-guides#prepare-the-project). Do not run `up` on a GitHub-backed service: it switches that service to uploaded source.

See the [full sveltekit guide](https://lizard.build/docs/framework-guides/sveltekit) for configuration and limits. Dependencies use the versions tested with this example; review updates before adopting them in your app.
