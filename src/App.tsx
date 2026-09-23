import Header from './components/Header'
import Counter from './components/Counter'
import TodoList from './components/TodoList'

function App() {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <section className="welcome">
          <h1>Welcome to My React App</h1>
          <h1>adding tag for checking cicd</h1>
          <p>This is a simple React application with a counter and todo list. Push code or open a PR to trigger the AI code review!</p>
        </section>
        
        <div className="widgets">
          <Counter />
          <TodoList />
        </div>
      </main>
    </div>
  )
}

export default App
