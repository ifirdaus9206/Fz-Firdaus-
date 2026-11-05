---
name: identity-aware-interaction
description: "Personalize responses using user identity documents."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
categories: [software-development]
metadata:
  hermes:
    tags: [identity, personalization, communication]
    related_skills: [hermes-agent]
---
# Identity-Aware Interaction

Personalize Hermes Agent responses by reading and adapting to user identity documents (SOUL.md, identity files) and expressed preferences.

## Trigger
Load this skill when:
- Starting a new session and you want to personalize responses based on user identity
- The user has provided identity documents (SOUL.md, identity-full.md, etc.)
- You need to adapt language, tone, or technical depth based on user background
- The user has expressed preferences for communication style (e.g., Bahasa Malaysia, concise responses)

## Steps
1. **Discover identity files**
   - Check `~/.hermes/SOUL.md` for agent's own soul/identity
   - Search `~/ULTIMATE_AI_PROJECT/identity/` and similar paths for identity documents
   - Use: `find ~/.hermes ~/ULTIMATE_AI_PROJECT -maxdepth 4 -type f \( -iname '*soul*' -o -iname '*identity*' \) 2>/dev/null`

2. **Extract key information from identity files**
   - Read each file with `read_file`
   - Extract:
     - Language preference (look for language indicators or content language)
     - User role/title (e.g., "GLOBAL AI AGENT CHIEF ARCHITECT")
     - Areas of expertise/domains of interest
     - Explicit communication preferences (e.g., "be concise", "use technical depth")
     - Version/timestamps to assess recency

3. **Adapt communication style**
   - **Language**: Respond in the user's preferred language if detectable (e.g., Bahasa Malaysia if identity files are in that language)
   - **Tone**: Match formality level (formal for titles/structured content, informal for casual language)
   - **Depth**: Adjust technical depth based on user role (executive summary vs. detailed technical steps)
   - **Examples**: Tailor suggestions and examples to user's expressed domains of interest

4. **Verify and maintain**
   - Check file modification timestamps; if stale, ask if user wants to use latest version
   - If multiple identity sources exist with conflicts, prefer most recent or explicitly indicated source
   - Periodically re-check identity files during long sessions for updates

## Pitfalls
- **Assuming static preferences**: Users may change language/depth preferences over time; re-check periodically
- **Overlooking multiple sources**: Identity may be split across several files (agent SOUL.md vs user identity files)
- **Misinterpreting role titles**: Titles like "Chief Architect" may imply strategic preference unless technical details requested
- **Over-personalization**: Don't assume all preferences apply to all contexts; verify when uncertain

## References
- See `references/identity-file-patterns.md` for common identity file structures and extraction patterns
- See `references/language-adaptation-guide.md` for techniques to adapt responses to different languages

## Success Indicators
- User acknowledges responses match their preferred language and communication style
- No need for user to repeat language or style requests
- Follow-up tasks are appropriately framed within user's expressed domains of interest
- User feels understood and receives appropriately leveled information

## Example
After reading `identity-full.md` revealing:
- Language: Bahasa Malaysia content
- Role: GLOBAL AI AGENT CHIEF ARCHITECT & MASTER STRATEGIST
- Expertise: 30-expert autonomous AI systems
- Preference: Technical depth with strategic context

The agent should:
1. Respond in Bahasa Malaysia (matching the document language)
2. Provide strategic overview first, then technical details if needed
3. Reference autonomous AI systems and multi-expert concepts when relevant
4. Match the formal yet visionary tone of the document