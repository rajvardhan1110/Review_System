# My React App with AI Code Review

A simple React application with an integrated AI-powered code review system that automatically reviews pull requests using Google Gemini.

## Project Structure

```
├── .github/workflows/       # CI/CD workflows
│   └── ai-code-review.yml   # AI review GitHub Action
├── src/
│   ├── components/          # React components
│   │   ├── Header.tsx
│   │   ├── Counter.tsx
│   │   └── TodoList.tsx
│   ├── code_review/         # AI review Python scripts
│   │   ├── review.py
│   │   ├── github_client.py
│   │   ├── repository_service.py
│   │   ├── diff_parser.py
│   │   └── gemini_service.py
│   ├── App.tsx
│   ├── App.css
│   └── main.tsx
├── review_prompt.md         # System prompt for Gemini
├── requirements.txt         # Python dependencies
├── package.json             # Node.js dependencies
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── index.html               # HTML entry point
```

---

## React App

### Running Locally

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```


The app runs at `http://localhost:5173` by default.

### Features

- **Header/Navbar** — Simple navigation bar
- **Counter** — Increment, decrement, and reset buttons
- **Todo List** — Add and remove todo items

---

## AI Code Review System

### How It Works

When you open a Pull Request or push new commits to an existing PR, the AI Code Review GitHub Action automatically:

1. **Triggers** on `pull_request` events (opened, synchronize, reopened)
2. **Extracts** only the changed lines from the PR diff
3. **Sends** the diff to Google Gemini (`gemini-3.1-flash-lite-preview`) for review
4. **Posts** inline comments on specific lines in the "Files changed" tab
5. **Posts** a summary comment on the PR "Conversation" tab

### Setup

1. Get a free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Add the key as a repository secret:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Create a new secret named `GEMINI_API_KEY` with your API key
3. That's it! The workflow uses the built-in `GITHUB_TOKEN` for posting comments.

### What Gets Reviewed

- Only changed/added lines (not full files)
- Skips binary files, lock files, and assets
- Focuses on: bugs, security issues, performance, and code quality

### Duplicate Prevention

- Before posting a new summary, the bot checks for existing summary comments and updates them instead of creating duplicates
- Review comments are posted as a single batch review

### Configuration

- **Model:** `gemini-3.1-flash-lite-preview` (free tier)
- **Temperature:** 0 (deterministic output)
- **Max comments:** 10 per review (to reduce noise)
- **Prompt:** Customizable in `review_prompt.md`

---

## License

MIT


### Configuration

- **Model:** `gemini-3.1-flash-lite-preview` (free tier)
- **Temperature:** 0 (deterministic output)
- **Max comments:** 10 per review (to reduce noise)
- **Prompt:** Customizable in `review_prompt.md`