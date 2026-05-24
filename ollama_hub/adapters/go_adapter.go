package llm

// Go LLM Adapter — import into any Go project.
// Provides LLM calls via local Ollama.

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

var ollamaHost = func() string {
	if h := os.Getenv("OLLAMA_HOST"); h != "" {
		return h
	}
	return "http://localhost:11434"
}()

const defaultModel = "llama3.2:1b"

// Client is the LLM client
type Client struct {
	Host         string
	DefaultModel string
	HTTP         *http.Client
}

// NewClient creates a new LLM client
func NewClient() *Client {
	return &Client{
		Host:         ollamaHost,
		DefaultModel: defaultModel,
		HTTP: &http.Client{
			Timeout: 300 * time.Second,
		},
	}
}

// Generate sends a prompt to the LLM and returns the response
func (c *Client) Generate(prompt, model, system string, temperature float32, maxTokens int) (string, error) {
	m := model
	if m == "" {
		m = c.DefaultModel
	}
	reqBody := map[string]interface{}{
		"model":   m,
		"prompt":  prompt,
		"system":  system,
		"stream":  false,
		"options": map[string]interface{}{"temperature": temperature, "num_predict": maxTokens},
	}
	data, err := json.Marshal(reqBody)
	if err != nil {
		return "", err
	}

	resp, err := c.HTTP.Post(c.Host+"/api/generate", "application/json", bytes.NewReader(data))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)
	if r, ok := result["response"].(string); ok {
		return r, nil
	}
	return "", fmt.Errorf("no response: %s", string(body))
}

// Chat sends a chat message to the LLM
func (c *Client) Chat(messages []map[string]string, model string) (string, error) {
	m := model
	if m == "" {
		m = c.DefaultModel
	}
	reqBody := map[string]interface{}{
		"model":    m,
		"messages": messages,
		"stream":   false,
	}
	data, _ := json.Marshal(reqBody)
	resp, err := c.HTTP.Post(c.Host+"/api/chat", "application/json", bytes.NewReader(data))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(body, &result)
	if msg, ok := result["message"].(map[string]interface{}); ok {
		if content, ok := msg["content"].(string); ok {
			return content, nil
		}
	}
	return "", nil
}

// CodeReview reviews Go code
func (c *Client) CodeReview(code string) (string, error) {
	system := "You are a senior Go engineer. Review for bugs, style, performance, security."
	prompt := fmt.Sprintf("Review this Go code:\n\n```\n%s\n```\n\nGive concise bullet points.", code)
	return c.Generate(prompt, "", system, 0.3, 600)
}

// ExplainCode explains code step by step
func (c *Client) ExplainCode(code string) (string, error) {
	prompt := fmt.Sprintf("Explain this code step by step:\n\n```\n%s\n```", code)
	return c.Generate(prompt, "", "You explain code clearly.", 0.3, 500)
}
