import { useState } from 'react'

function Counter() {
  const [count, setCount] = useState(0)

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

export default Counter
