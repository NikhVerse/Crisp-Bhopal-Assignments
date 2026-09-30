# Reflection Report - PromptCraft AI Studio

## Design Decisions
1. **Editorial Typography Hierarchy**: We shifted the design language entirely to a whitespace-driven, typographic-led structure. Rather than packing settings and outputs inside dense cards or bordered box wrappers, the app relies on thin 1px `#E5E5E5` lines and generous spacing (~2-3rem) to demarcate blocks, providing a quiet, writing-focused canvas like Notion or Linear.
2. **Minimal Palette & Accent Contrasts**: Saturated colored tabs and bright violet/indigo gradient buttons were rejected. We used a pure light background (`#FAFAFA` for canvas, `#FFFFFF` for sidebar panel) with high-contrast, deep charcoal (`#1A1A1A`) active states and buttons.
3. **Streamlit Component Overrides**: We injected custom CSS targeting classes like `[data-baseweb="tab"]` and `div.stButton > button` to override Streamlit's default pill-style selectors and rounded corner buttons, turning them into flat, square-edged, minimal controls with a thin underline indicator.
4. **Session-Stored Persisted Outputs**: When generating text in a specific tab, Streamlit normally reruns the page. If the user clicks another tab and returns, local variables are lost. To maintain the generated output and download state, we bound all generation outputs to `st.session_state.outputs` dynamically.

## Challenges
1. **Streamlit CSS Target Audits**: Standard Streamlit classes (like `.stTabs`) can sometimes be complex to style reliably because elements are rendered inside Web Components or iframe-like wrappers. Finding the correct elements (e.g. `[data-baseweb="tab-list"]` and `div[data-testid="stVerticalBlockBorderWrapper"]`) required fine-tuned DOM investigation.
2. **Interactive Testing without Live Keys**: Testing browser interactions and taking screenshots without hardcoding real API keys or assuming the user has configured local `.env` values.
   - *Solution*: We built a dedicated **Mock Mode** inside `utils.py`. Setting the API key parameter to `"mock"` (or leaving it blank) triggers realistic simulated responses tailored to the specific prompts, allowing end-to-end user flows and visual audits.

## What Was Learned
1. **Unifying API Clients**: The OpenAI Python SDK is robust enough to call alternative providers (like Groq) simply by swapping the `base_url` parameter, allowing us to keep a single clean function `call_llm()` for both providers.
2. **Streamlit Custom Branding**: Streamlit applications do not have to look like standard data dashboards. With a moderate amount of custom CSS injection, you can build premium, editorial, minimalist productivity tools.

## Future Improvements
1. **Persistent Local History**: Currently, query history is session-based. In the future, we could store request history in a local SQLite file (or browser local storage) so that users do not lose history between browser refreshes.
2. **Token and Cost Tracking**: Display token usage metrics (prompt tokens, completion tokens) alongside latency metrics for both OpenAI and Groq APIs to help users optimize prompt designs and control costs.
3. **Structured Outputs**: Use OpenAI's json-mode or Pydantic structured output models to enforce strict schema requirements for tools like the Code Explainer or Interview Prep generator, making it easier to export outputs in CSV/JSON formats.
