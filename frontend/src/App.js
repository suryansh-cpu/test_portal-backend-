import React, { useState } from "react";
import axios from "axios";

function App() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // const res = await axios.post("http://127.0.0.1:5000", { message: input });
      const res = await axios.post("http://127.0.0.1:5000/api/data", { message: input });
      setResponse(res.data.reply);
    } catch (err) {
      console.error(err);
      setResponse("Error contacting Flask server");
    }
  };

  return (
    <div style={{ margin: "2rem" }}>
      <h2>React ↔ Flask Demo</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter message"
        />
        <button type="submit">Send</button>
      </form>
      <p><strong>Response:</strong> {response}</p>
    </div>
  );
}

export default App;
