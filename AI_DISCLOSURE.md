# AI Use Disclosure

## AI assistance during development

An AI coding assistant (OpenAI Codex) was used to help draft and edit application code, user interface text, setup instructions, and deployment configuration. The project team supplied the product concept and troubleshooting data. AI assistance was used as a development aid; the team remains responsible for reviewing the code, data, and user-facing guidance before release.

## AI used by the application

The current application does not call OpenAI or another generative AI model to answer users. It uses deterministic text matching to find the closest item in the supplied troubleshooting dataset. Severity labels, device-model detection, and the small Hinglish phrase map are rule-based heuristics; they are not model-generated diagnoses.

## Data and limitations

The troubleshooting content and deeplink catalog were provided for this project. The supplied content includes TechCorp/Nexa names, and the deeplink URIs are masked placeholders. The links therefore do not open real Samsung settings screens, and the content has not been established as verified Samsung guidance. Results can be incomplete or irrelevant and should be checked against the user's exact device and an authoritative support source.

## User input

The application has no built-in conversation database and does not intentionally send prompts to a generative AI provider. When hosted on Vercel, requests are processed by the app through Vercel's infrastructure. Review the hosting provider's current privacy and logging terms before publishing the service for public use.

If a generative AI service, new data source, or persistent conversation storage is added later, this disclosure should be updated before that version is released.
