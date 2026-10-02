declare module 'claude-code' {
  interface PluginState {
    'agent-effort': {
      /** The agent an Agent call started, keyed by the call's tool_use_id. */
      agentOfCall: StateFamily<string>
      /** The effort an agent's latest model request carried, keyed by its agentId. */
      effortOfAgent: StateFamily<string>
      /** The agents launched in or moved to the background, by agentId, in launch order. */
      background: string[]
      /** Whether an agent's turn is running: true from its first request until its turn completes. */
      isRunning: StateFamily<boolean>
    }
  }
}
