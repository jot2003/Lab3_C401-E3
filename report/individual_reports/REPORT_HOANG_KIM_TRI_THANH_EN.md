# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hoang Kim Tri Thanh
- **Student ID**: 2A202600372
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/tools/weather.py`, `docs/OPENWEATHER_SETUP_VI.md`, `app.py`.
- **Code Highlights**:
  - Improved weather query retry with city-name variants.
  - Added direct verification links and clearer weather error messages.
  - Updated citation rendering based on tool observations.
- **Documentation**:
  - Synchronized OpenWeather setup guidance to support faster team debugging.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: The agent sometimes hallucinated weather limitations instead of following real observation data.
- **Log Source**: `logs/YYYY-MM-DD.log` with `AGENT_LLM_STEP` and `AGENT_OBSERVATION` events.
- **Diagnosis**: The system prompt was not strict enough, so the model invented technical API constraints.
- **Solution**: Tightened prompt instructions to require observation-grounded explanations only.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: The `Thought` step helps break tasks into clear sub-steps before answering.
2. **Reliability**: The agent can be less stable when tools repeatedly fail or external APIs timeout.
3. **Observation**: Observation feedback is critical for correcting the next action instead of guessing.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Add weather caching by city/time window.
- **Safety**: Standardize user-facing error messages while preserving factual details.
- **Performance**: Use shorter prompt templates for weather-only scenarios to reduce token usage.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
