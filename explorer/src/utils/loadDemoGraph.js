// Loads the bundled demo graph so visitors can explore VibeGraph with zero
// setup — no upload, no API key. Shared by the empty-state CTA and the upload
// modal's "Try with a Demo Project" button so both fetch the same way.
export async function loadDemoGraph() {
    let res = await fetch('/demo_graph_data.json');
    if (!res.ok) {
        res = await fetch('/graph_data.json');
    }
    if (!res.ok) {
        throw new Error(`Demo file not found on the server (HTTP ${res.status})`);
    }
    return res.json();
}

// Loads the hand-authored, pre-baked demo AI content (explanations + canned chat)
// so the demo shows AI value with zero key and zero network to the AI endpoints.
// Best-effort: any failure returns null and the caller falls back to live/walled AI.
export async function loadDemoAiContent() {
    try {
        const res = await fetch('/demo_ai_content.json');
        if (!res.ok) {
            return null;
        }
        return await res.json();
    } catch {
        return null;
    }
}
