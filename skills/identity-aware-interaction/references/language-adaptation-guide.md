# Language Adaptation Guide

This reference provides techniques for adapting Hermes Agent responses to different languages and communication styles.

## Language Detection Techniques
1. **Content Analysis**: Check the primary language of identity documents
2. **Explicit Markers**: Look for language indicators in frontmatter or content
3. **User Signals**: Note if user has previously responded in a specific language
4. **Fallback**: Default to English if language cannot be determined

## Bahasa Malaysia Adaptation
When responding in Bahasa Malaysia:
- Use formal greetings and closings appropriate to the context
- Match the level of formality in the identity documents
- Technical terms can remain in English when commonly used in professional contexts
- Use Malaysian spelling conventions (e.g., "sistem" not "system" in formal contexts)
- Consider cultural context in examples and references

## English Adaptation
When responding in English:
- Match the formality level detected in identity documents
- Adjust technical depth based on user role/expertise
- Use appropriate professional tone for titles like "Chief Architect" or "Master Strategist"

## Tone and Formality Adaptation
Based on detected formality in identity documents:

### Formal (when documents use titles, structured sections, formal language):
- Use proper greetings and closings
- Provide structured responses with clear sections
- Reference user's titles and roles when relevant
- Use complete sentences and professional vocabulary
- Avoid slang, contractions, and overly casual expressions

### Informal (when documents use casual language, personal expressions):
- Use friendly but respectful tone
- Can use contractions and simpler sentence structures
- Still maintain professionalism and clarity
- Match the user's energy level and communication style

## Depth Adaptation
Adjust technical depth based on user role:

### Executive/Strategic Roles (e.g., Chief Architect, Master Strategist):
- Start with high-level overview and strategic implications
- Provide executive summary first
- Offer to dive into technical details upon request
- Focus on business impact, ROI, and strategic alignment
- Use visionary and forward-looking language

### Technical Roles (e.g., Engineer, Developer):
- Can start with technical details if appropriate
- Provide implementation-level information
- Include code examples, architectures, and technical specifications
- Balance depth with clarity

### Hybrid Roles:
- Provide both strategic overview and technical details
- Clearly separate sections for different audiences
- Allow user to guide focus through follow-up questions

## Communication Preference Indicators
Adapt based on explicit statements in identity documents:
- "be concise" → Provide brief, to-the-point responses
- "provide technical depth" → Include detailed technical information
- "use formal language" → Maintain formal tone throughout
- "respond in [language]" → Use specified language
- "avoid jargon" → Explain technical terms or avoid them when possible
- "include examples" → Provide practical examples and use cases

## Verification and Feedback
- Periodically check if adaptation matches user expectations
- Ask for feedback on language and tone if unsure
- Monitor user responses for cues about preferred style
- Be ready to re-adapt if user signals a change in preference

## Example Adaptation Flow
1. Read identity-full.md detects:
   - Language: Bahasa Malaysia (document is in Bahasa Malaysia)
   - Role: GLOBAL AI AGENT CHIEF ARCHITECT & MASTER STRATEGIST
   - Preference: Technical depth with strategic context (from description)
2. Agent responds:
   - In Bahasa Malaysia (matching document language)
   - Starts with strategic overview (matching chief architect role)
   - Provides technical details when discussing AI systems (matching expertise)
   - Uses formal yet visionary tone (matching title and description)