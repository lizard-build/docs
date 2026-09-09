import{json}from'@sveltejs/kit';export function GET(){return json({framework:'svelte-node',time:Date.now()});}
