# React 18 & Vite Architecture

## Best Practices
1. **Component Modularity**: Keep components small, functional, and single-purpose (`src/components/`).
2. **State Management**: Use `useState` for local UI state and React Context or custom hooks for global state.
3. **HTTP Requests**: Use `axios` or native `fetch` inside `useEffect` or dedicated service modules (`src/services/api.js`).
4. **Styling**: Utilize Tailwind CSS utility classes and modern flexbox/grid layouts.
5. **Vite Build**: Bundle using `vite build` targeting ESNext standards.
