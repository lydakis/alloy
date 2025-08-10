# Alloy Library Specification v1.0

## Core Philosophy

**"Python for logic. English for intelligence."**

Alloy enables hybrid programming where Python handles deterministic computation and English specifies intelligent behavior. Commands (AI-powered, non-deterministic) are distinguished from methods (Python, deterministic) through clear conventions.

## Installation

```bash
pip install alloy-ai
```

## Core API (v1.0)

### 1. Commands - English Specifications with Python Preprocessing

Commands are decorated functions that return English specifications (prompts). The function body can perform arbitrary Python computation before returning the specification.

```python
from alloy import command
from dataclasses import dataclass

# Simple command - declare output type in decorator
@command(output=float)
def ExtractPrice(text: str) -> str:  # Returns prompt string
    """Extract price from text."""
    return f"Extract the price from: {text}"

# Command with structured output
@dataclass
class Analysis:
    summary: str
    confidence: float
    key_points: list[str]

@command(output=Analysis)
def AnalyzeData(data: dict) -> str:  # Returns prompt string
    """Analyze data and return structured insights."""
    # Python preprocessing
    cleaned_data = clean_data(data)
    stats = calculate_statistics(cleaned_data)
    
    # Return English specification
    return f"""
    Analyze this data:
    Statistics: {stats}
    Sample: {cleaned_data[:100]}
    Provide comprehensive analysis.
    """

# At call sites, type checkers see the output type
price = ExtractPrice("$49.99")  # price: float
analysis = AnalyzeData(data)    # analysis: Analysis
```

#### Naming Convention

Commands use PascalCase to visually distinguish them from regular Python functions:
- `calculate_tax()` - Deterministic Python function
- `ExtractTaxInfo()` - Non-deterministic AI command

#### Type Annotations

Commands return prompt strings but output structured data. Declare the output type in the decorator:
- Functions return `-> str` (the prompt)
- `output=` parameter specifies the actual output type
- Alloy's type stubs ensure call sites see the correct type
- No type checker errors, no suppressions needed
- Supports: primitives, dataclasses, TypedDict, Pydantic models (v1.1)

### 2. Tools - Python Functions with Contracts

Tools are Python functions that commands can call. Optional contracts teach the AI how to use them correctly.

```python
from alloy import tool, require, ensure

# Simple tool
@tool
def search_web(query: str) -> list:
    """Search the web for information."""
    return web_api.search(query)

# Tool with contracts (optional but recommended)
@tool
@require(lambda url: url.startswith("https://"), "URL must be HTTPS")
@ensure(lambda result: result.status_code == 200, "Request must succeed")
def fetch_url(url: str) -> Response:
    return requests.get(url)

# Contracts teach workflows
@tool
def validate_data(data: dict) -> dict:
    data['validated_at'] = datetime.now()
    return data

@tool
@require(lambda data: 'validated_at' in data, "Must run validate_data first")
def save_to_production(data: dict) -> bool:
    # AI learns it must validate before saving
    return production_db.save(data)

# Commands with tools
@command(output=str, tools=[search_web, fetch_url])
def ResearchTopic(topic: str) -> str:
    """Research a topic using web sources."""
    return f"Research {topic} thoroughly using available tools"
```

### 3. Ask - Exploratory Interface

For open-ended exploration without structured outputs.

```python
from alloy import ask

# Simple exploration
answer = ask("What is quantum computing?")

# With tools
response = ask(
    "Find recent news about AI", 
    tools=[search_web, fetch_url]
)

# With context
explanation = ask(
    "Explain this error", 
    context={"error": error_message, "code": code_snippet}
)
```

## Execution Modes

Alloy automatically detects execution mode based on function definition:
- `def` → Synchronous command
- `async def` → Asynchronous command

Both support streaming, and sync commands can optionally be called async.

### Sync (Default)

```python
@command(output=float)
def ExtractPrice(text: str) -> str:
    return f"Extract price from: {text}"

# Default is synchronous - simple and works everywhere
result = ExtractPrice("Product costs $49.99")  # result: float
answer = ask("Explain this concept")  # answer: str
```

### Async

```python
# Async commands use async def
@command(output=float)
async def ExtractPriceAsync(text: str) -> str:
    return f"Extract price from: {text}"

# Async with preprocessing
@command(output=Analysis)
async def AnalyzeWithContext(data: dict) -> str:
    # Async operations in prompt building
    market_data = await fetch_market_data()
    user_context = await get_user_context()
    
    return f"""
    Analyze {data}
    Market: {market_data}
    Context: {user_context}
    """

# Natural async usage
result = await ExtractPriceAsync("Product costs $49.99")
analysis = await AnalyzeWithContext(data)

# Parallel execution
results = await asyncio.gather(
    AnalyzeWithContext(q1_data),
    AnalyzeWithContext(q2_data),
    AnalyzeWithContext(q3_data)
)

# Sync commands can still be called async if needed
@command(output=float)
def ExtractPrice(text: str) -> str:
    return f"Extract price from: {text}"

# Optional: sync commands have .async_() for convenience
result = await ExtractPrice.async_("$49.99")
```

### Streaming

```python
# Stream responses as they generate
for chunk in ask.stream("Write a detailed explanation"):
    print(chunk, end='', flush=True)

# Stream from sync command
@command(output=str)
def GenerateReport(data: dict) -> str:
    return f"Generate report for: {data}"

for chunk in GenerateReport.stream(data):
    update_ui(chunk)

# Async streaming command
@command(output=str)
async def GenerateReportAsync(data: dict) -> str:
    context = await fetch_context()
    return f"Generate report for {data} with context: {context}"

async for chunk in GenerateReportAsync.stream(data):
    await update_ui(chunk)

# Async streaming with ask
async for chunk in ask.stream_async("Tell me a story"):
    await display(chunk)
```

## Configuration

```python
from alloy import configure

# Global defaults
configure(
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000,
    default_system="You are a helpful assistant"
)

# Per-command configuration
@command(
    output=str,
    model="claude-3.5-sonnet",
    temperature=0.9,
    system="You are a creative writer"
)
def WriteCreatively(prompt: str) -> str:
    return f"Write creatively about: {prompt}"

# Runtime overrides
response = ask(
    "Explain simply", 
    model="gpt-3.5-turbo",
    temperature=0.3
)
```

## Model Support

Alloy automatically uses the best execution strategy per model:

### Native Tool Calling
- **OpenAI**: GPT-4, GPT-3.5 (native function calling)
- **Anthropic**: Claude 3, Claude 3.5 (native tool use)
- **Google**: Gemini Pro (native function calling)

### ReAct Fallback
- **Meta**: Llama 3.1, Llama 3.2
- **Mistral**: Mixtral (via their API)
- **Local Models**: Any Ollama/llama.cpp model

```python
# Same API regardless of model
@command(output=Analysis, tools=[search, calculate])
def Analyze(data: dict) -> str:
    return f"Analyze: {data}"

# Automatically uses:
# - Native tools for GPT-4/Claude
# - ReAct loop for Llama
# - Best available for each model
```

## Error Handling

```python
from alloy import CommandError, ToolError

@command(output=float)
def ExtractPrice(text: str) -> str:
    return f"Extract price from: {text}"

try:
    result = ExtractPrice("No price here")
except CommandError as e:
    # Handle extraction failure
    print(f"Could not extract: {e}")

# Tools raise specific errors
try:
    result = fetch_url("invalid-url")
except ToolError as e:
    # Contract violation
    print(f"Tool failed: {e}")

# Retry logic
@command(output=float, retry=3, retry_on=CommandError)
def ReliableExtraction(text: str) -> str:
    return f"Extract price from: {text}"
```

## Type System Integration

Alloy ships with complete type stubs that make commands work seamlessly with type checkers:

```python
# alloy/__init__.pyi (shipped with library)
from typing import Callable, ParamSpec, TypeVar, overload, Coroutine
P = ParamSpec("P")
T = TypeVar("T")

# Sync command overloads
@overload
def command(__func: Callable[P, str], /, *, output: type[T] | None = ...) -> Callable[P, T]: ...
@overload
def command(*, output: type[T] | None = ...) -> Callable[[Callable[P, str]], Callable[P, T]]: ...

# Async command overloads  
@overload
def command(__func: Callable[P, Coroutine[Any, Any, str]], /, *, output: type[T] | None = ...) -> Callable[P, Coroutine[Any, Any, T]]: ...
@overload
def command(*, output: type[T] | None = ...) -> Callable[[Callable[P, Coroutine[Any, Any, str]]], Callable[P, Coroutine[Any, Any, T]]]: ...
```

This ensures that:
- Functions return `-> str` (the prompt) in implementation
- `async def` commands are recognized as async
- Call sites see the correct output type and async behavior
- Full IDE autocomplete and type checking
- No suppressions or ignores needed
- Works with mypy, pyright, pylance, and all major type checkers

## Complete Example

```python
from alloy import command, tool, ask, configure
from dataclasses import dataclass
import asyncio

# Configure defaults
configure(model="gpt-4", temperature=0.7)

# Define tools
@tool
@ensure(lambda r: len(r) > 0, "Must find results")
def search_products(query: str) -> list:
    return product_api.search(query)

@tool
def calculate_discount(price: float, discount_percent: float) -> float:
    return price * (1 - discount_percent / 100)

# Define structured output
@dataclass
class ProductRecommendation:
    product_name: str
    original_price: float
    discount_price: float
    reasoning: str

# Sync command
@command(output=ProductRecommendation, tools=[search_products, calculate_discount])
def RecommendProduct(category: str, budget: float) -> str:
    """Find and recommend a product within budget."""
    return f"""
    Find the best {category} product under ${budget}.
    Search for options, calculate discounts if applicable.
    Recommend the best value option.
    """

# Async command with preprocessing
@command(output=ProductRecommendation, tools=[search_products, calculate_discount])
async def RecommendProductAsync(category: str, budget: float) -> str:
    """Find product with market context."""
    # Async preprocessing
    market_trends = await fetch_market_trends(category)
    user_prefs = await get_user_preferences()
    
    return f"""
    Find the best {category} product under ${budget}.
    Consider market trends: {market_trends}
    User preferences: {user_prefs}
    Search for options, calculate discounts, recommend best value.
    """

# Use sync command
recommendation = RecommendProduct("laptop", 1500)
print(f"Recommended: {recommendation.product_name}")
print(f"Price: ${recommendation.discount_price}")

# Use async command
async def get_recommendations():
    # Direct async calls
    laptop = await RecommendProductAsync("laptop", 1500)
    
    # Parallel async execution
    results = await asyncio.gather(
        RecommendProductAsync("laptop", 1500),
        RecommendProductAsync("phone", 800),
        RecommendProductAsync("tablet", 600)
    )
    return results

# Streaming for real-time UI
for chunk in ask.stream(
    "Explain why this product is good",
    context=recommendation
):
    print(chunk, end='', flush=True)

# Async streaming
async def stream_report():
    @command(output=str)
    async def GenerateDetailedReport(product: ProductRecommendation) -> str:
        reviews = await fetch_reviews(product.product_name)
        return f"Generate detailed report for {product.product_name} with reviews: {reviews}"
    
    async for chunk in GenerateDetailedReport.stream(recommendation):
        await update_ui(chunk)
```

## State Management (Not Core)

State is the caller's responsibility. Alloy provides optional helpers:

```python
# Explicit state management
conversation_history = []

def chat_with_memory(message: str) -> str:
    conversation_history.append({"role": "user", "content": message})
    
    @command(output=str)
    def Respond(message: str, history: list) -> str:
        return f"""
        Conversation history: {history}
        Respond to: {message}
        """
    
    response = Respond(message, conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    return response

# Async version with context fetching
async def chat_with_context(message: str) -> str:
    @command(output=str)
    async def RespondWithContext(message: str) -> str:
        # Fetch context asynchronously
        user_profile = await get_user_profile()
        recent_topics = await get_recent_topics()
        
        return f"""
        User profile: {user_profile}
        Recent topics: {recent_topics}
        Respond to: {message}
        """
    
    return await RespondWithContext(message)
```

## Future Capabilities (v2+)

### Memory & Learning (v2.0)
```python
# Commands that improve through use
memory = Memory(learn=True)

@command(output=str, memory=memory)
def EvolvingCommand(input: str) -> str:
    # Accumulates patterns and learns from mistakes
    return f"Process: {input}"

# After 1000 calls, command has learned patterns
print(memory.patterns_learned)  # 47 patterns identified
```

### Local Model Support (v2.0)
```python
# Configure for local models
configure(
    model="local:llama-3.1-8b",
    inference_server="http://localhost:8080"
)

# Same API, runs locally
result = ExtractPrice("$49.99")  # ~100ms latency
```

### MCP Integration (v3.0)
```python
# Tools and resources from MCP servers (future)
@command(output=Analysis, tools=mcp.discover_tools())
def AnalyzeWithContext(query: str) -> str:
    return f"Analyze: {query}"
```

### Dynamic Interface Generation (v3.0)
```python
# Generate UI components on demand (future)
@command(output=HTMLComponent, model="local:o4-mini")
def GenerateInterface(user_intent: str) -> str:
    return f"Create interface for: {user_intent}"
```

## Design Principles

1. **Explicit over implicit** - PascalCase shows non-determinism
2. **Python for logic** - Use Python for data manipulation
3. **English for intelligence** - Commands are English specifications
4. **Progressive enhancement** - Start simple, add AI gradually
5. **Model agnostic** - Same API regardless of model
6. **Type safe** - Full IDE support through type hints
7. **Batteries included** - Works out of the box
8. **Escape hatches** - Can access raw prompts/responses when needed

## Implementation Priority

### v1.0 (Launch)
- [x] Core decorators: @command, @tool
- [x] Output type in decorator pattern
- [x] Type stubs for IDE support  
- [x] ask() for exploration
- [x] Native tool support + ReAct fallback
- [x] Sync/async/streaming execution
- [x] Basic error handling
- [x] Model configuration

### v1.1 (Polish)
- [ ] Pydantic model support
- [ ] TypedDict support
- [ ] Retry logic
- [ ] Token tracking
- [ ] Cost estimation
- [ ] Better error messages
- [ ] Optional mypy plugin for alternative patterns

### v2.0 (Enhancement)
- [ ] Memory system
- [ ] Local model support
- [ ] Pattern learning
- [ ] Caching layer
- [ ] Telemetry/observability

### v3.0+ (Future)
- [ ] MCP integration
- [ ] Dynamic UI generation
- [ ] Multi-agent coordination
- [ ] Distributed command sharing

## Summary

Alloy makes AI-powered functions as simple as regular Python functions. Commands are English, tools are Python, and the complexity of agents, chains, and prompts disappears. The library that proves AI can be just another function call.