import { Chat } from "./components/Chat";
import { useSSE } from "./hooks/useSSE";

function App() {
  const { messages, isLoading, sendMessage } = useSSE();

  return <Chat messages={messages} isLoading={isLoading} onSend={sendMessage} />;
}

export default App;
