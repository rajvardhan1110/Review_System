# AI Code Review System — File Documentation (Part 3: Frontend & Config)

---

# File 8: `index.html`

## 1. Purpose
The HTML entry point for the Vite+React application. Vite uses this file as the starting template and injects the bundled JavaScript.

## 2. Location
**Path:** `index.html` (project root)  
Vite requires `index.html` at the project root (not in `public/` or `src/`).

## 3. Dependencies
- **References:** `/src/main.tsx` via `<script type="module">`
- **Used by:** Vite dev server and build process

## 4. Code Walkthrough
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />                    <!-- Character encoding -->
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />  <!-- Favicon -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />  <!-- Responsive -->
    <title>My React App</title>
  </head>
  <body>
    <div id="root"></div>                        <!-- React mounts here -->
    <script type="module" src="/src/main.tsx"></script>  <!-- Entry script -->
  </body>
</html>
```

- `type="module"` enables ES module imports (required for Vite)
- `<div id="root">` is the mount point for `ReactDOM.createRoot()`
- Vite transforms this at build time, replacing the script tag with the bundled output

## 5. Summary
- Standard Vite HTML entry point
- Contains the `#root` div where React renders
- Loads `main.tsx` as an ES module
- Minimal — no inline styles or scripts

---

# File 9: `main.tsx`

## 1. Purpose
React's JavaScript entry point. Initializes React and renders the `App` component into the DOM.

## 2. Location
**Path:** `src/main.tsx`

## 3. Code Walkthrough
```tsx
import React from 'react'                    // React core
import ReactDOM from 'react-dom/client'      // DOM-specific rendering
import App from './App'                       // Root component
import './App.css'                            // Global styles (side-effect import)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>                          // Enables dev-time warnings
    <App />                                   // Root component
  </React.StrictMode>,
)
```

- `!` after `getElementById('root')` is TypeScript's non-null assertion (we know `#root` exists)
- `React.StrictMode` doesn't affect production; in dev, it double-renders to catch bugs
- CSS import is a side-effect — no variable exported, just applies styles globally

## 4. Summary
- Bootstraps React into `#root`
- Imports global CSS
- Uses StrictMode for development safety
- Standard Vite+React boilerplate

---

# File 10: `App.tsx`

## 1. Purpose
Root React component. Composes the page layout using `Header`, `Counter`, and `TodoList` child components.

## 2. Location
**Path:** `src/App.tsx`

## 3. Code Walkthrough
```tsx
import Header from './components/Header'
import Counter from './components/Counter'
import TodoList from './components/TodoList'

function App() {
  return (
    <div className="app">
      <Header />                              // Navigation bar
      <main className="main-content">
        <section className="welcome">
          <h1>Welcome to My React App</h1>
          <p>...Push code or open a PR to trigger the AI code review!</p>
        </section>
        <h1> hey this is demo branch</h1>     // Demo line (for testing the bot)
        <div className="widgets">
          <Counter />                          // Counter widget
          <TodoList />                         // Todo list widget
        </div>
      </main>
    </div>
  )
}
export default App
```

- The `<h1> hey this is demo branch</h1>` line is intentionally placed to test the AI review bot — it's a "bad practice" line (duplicate `<h1>`, informal text) that the bot should flag.
- No state management here — each child component manages its own state.

## 4. Summary
- Root component composing Header + Counter + TodoList
- Contains a test line for the AI reviewer
- Uses CSS class names matching `App.css`
- Stateless — delegates to children

---

# File 11: `App.css`

## 1. Purpose
All CSS styles for the React application. Uses a single-file approach with section comments.

## 2. Location
**Path:** `src/App.css`

## 3. Key Style Sections

| Section | Selector(s) | Purpose |
|---------|------------|---------|
| Reset | `*` | Zero out margins, padding; set `box-sizing` |
| Body | `body` | System font stack, light gray background |
| Layout | `.app`, `.main-content` | Flexbox column layout, max-width 1200px |
| Header | `.header`, `.header nav` | Purple gradient background, flex nav |
| Welcome | `.welcome` | Centered hero section |
| Widgets | `.widgets` | CSS Grid, 2 columns (1 on mobile) |
| Card | `.card` | White card with border-radius and shadow |
| Counter | `.counter-*` | Large number display, colored buttons |
| Todo | `.todo-*` | Input field, list items, remove buttons |

**Notable:**
- Responsive: `@media (max-width: 768px)` switches grid to single column
- Header uses `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` — purple gradient
- Button active state: `transform: scale(0.95)` — subtle press feedback

## 4. Summary
- Single CSS file for the entire React app
- Mobile-responsive grid layout
- Gradient header, card-based widgets
- Micro-interactions (hover, active states)
- System font stack (no external fonts)

---

# File 12: `Header.tsx`

## 1. Purpose
Simple navigation bar component.

## 2. Location: `src/components/Header.tsx`

## 3. Code
```tsx
function Header() {
  return (
    <header className="header">
      <nav>
        <h2>MyReactApp</h2>
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </nav>
    </header>
  )
}
export default Header
```

- Stateless functional component (no `useState`)
- `href="#"` — placeholder links (demo app)
- Uses semantic HTML (`<header>`, `<nav>`)

---

# File 13: `Counter.tsx`

## 1. Purpose
Interactive counter widget demonstrating React state management.

## 2. Location: `src/components/Counter.tsx`

## 3. Code Walkthrough
```tsx
import { useState } from 'react'

function Counter() {
  const [count, setCount] = useState(0)    // State: number, starts at 0

  return (
    <div className="card">
      <h3>Counter</h3>
      <div className="counter-display">{count}</div>
      <div className="counter-buttons">
        <button className="btn-decrement" onClick={() => setCount(count - 1)}>
          − Decrement
        </button>
        <button className="btn-reset" onClick={() => setCount(0)}>
          Reset
        </button>
        <button className="btn-increment" onClick={() => setCount(count + 1)}>
          + Increment
        </button>
      </div>
    </div>
  )
}
```

- `useState(0)` initializes counter to 0
- Three buttons: decrement (-1), reset (to 0), increment (+1)
- **Note:** Uses `setCount(count - 1)` instead of `setCount(prev => prev - 1)`. The functional form is safer with rapid clicks but works fine here.

---

# File 14: `TodoList.tsx`

## 1. Purpose
Interactive todo list demonstrating state management, form handling, and list rendering.

## 2. Location: `src/components/TodoList.tsx`

## 3. Code Walkthrough
```tsx
const [todos, setTodos] = useState<string[]>([])   // Array of todo strings
const [input, setInput] = useState('')               // Current input value

const addTodo = () => {
  const trimmed = input.trim()                       // Remove whitespace
  if (trimmed) {                                     // Don't add empty todos
    setTodos([...todos, trimmed])                    // Append to array
    setInput('')                                     // Clear input
  }
}

const removeTodo = (index: number) => {
  setTodos(todos.filter((_, i) => i !== index))      // Remove by index
}

const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Enter') addTodo()                   // Enter key = submit
}
```

- TypeScript generic: `useState<string[]>([])` — array of strings
- `filter((_, i) => i !== index)` — removes item at given index
- Enter key handler for UX convenience
- Empty state: "No todos yet. Add one above!"
- **Note:** Using index as `key` is acceptable here since items don't have unique IDs and aren't reordered.

---

# File 15: `package.json`

## 1. Purpose
Node.js project manifest. Defines dependencies, scripts, and project metadata.

## 2. Key Fields
| Field | Value | Purpose |
|-------|-------|---------|
| `name` | `"my-react-app"` | Package identifier |
| `private` | `true` | Prevents accidental npm publish |
| `type` | `"module"` | Enables ES module syntax (`import/export`) |
| `scripts.dev` | `"vite"` | Starts dev server (`npm run dev`) |
| `scripts.build` | `"tsc && vite build"` | Type-check then bundle |
| `dependencies` | `react`, `react-dom` | Runtime libraries |
| `devDependencies` | TypeScript, Vite, React types, plugin | Build tools |

---

# File 16: `tsconfig.json`

## 1. Purpose
TypeScript compiler configuration.

## 2. Key Options
| Option | Value | Why |
|--------|-------|-----|
| `target` | `ES2020` | Modern JS features (optional chaining, etc.) |
| `jsx` | `react-jsx` | Automatic JSX transform (no `import React`) |
| `strict` | `true` | Maximum type safety |
| `noEmit` | `true` | Vite handles compilation; tsc only type-checks |
| `moduleResolution` | `bundler` | Matches Vite's resolution strategy |
| `noUnusedLocals` | `true` | Catches dead code |
| `include` | `["src"]` | Only type-check source files |

---

# File 17: `vite.config.ts`

## 1. Purpose
Vite build tool configuration.

## 2. Code
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
```
Minimal config — just enables the React plugin for JSX/TSX support and Fast Refresh (hot module replacement during development).

---

# File 18: `requirements.txt`

## 1. Purpose
Python dependency declaration for the review bot.

## 2. Content
```
requests
```
Single dependency: the `requests` HTTP library. Used by `gemini_service.py` and `github_client.py` for all API calls.

**Why not pin a version?** Simplicity — for a CI/CD script, latest `requests` is fine. Production systems should pin: `requests==2.31.0`.

---

# File 19: `README.md`

## 1. Purpose
Repository documentation visible on the GitHub page. Explains project structure, setup, and how the bot works.

## 2. Key Sections
- Project structure tree
- React app setup (`npm install`, `npm run dev`)
- AI Code Review system explanation
- Setup instructions (adding `GEMINI_API_KEY` secret)
- What gets reviewed and what's skipped
- Configuration details

---

# File 20: `PROJECT_OVERVIEW.md`

## 1. Purpose
Internal comprehensive documentation covering problem statement, solution design, tech stack, architecture, comparisons with other tools, and future enhancements.

## 2. Location: `src/PROJECT_OVERVIEW.md`

## 3. Key Contents
- Problem: Manual reviews are slow, inconsistent, error-prone
- Solution: AI-powered automated bot using Gemini
- Architecture diagram (ASCII)
- Design decisions table
- Comparison with GitHub Copilot, CodeRabbit, SonarCloud
- Future enhancements list
