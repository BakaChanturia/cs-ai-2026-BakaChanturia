## Model Comparison Observations

The outputs from the two models were noticeably different in style and detail.  
The **gemini-3-flash-preview** model produced a longer and more detailed response, including both a basic recursive implementation and an optimized version using memoization with additional explanations.  
The **gemini-3.1-flash-lite-preview** model generated a shorter and more concise answer that still solved the problem but with less extra discussion.  

In terms of performance, the **flash-lite model was significantly faster**, with a latency of **2162 ms**, compared to **6364 ms** for the flash model.  
The token counts also reflected this difference: the flash model produced many more output tokens because its explanation was longer, while the flash-lite model stayed more compact.  

One interesting observation was that the flash model suggested an **optimized implementation using `lru_cache`**, even though the prompt only asked for a recursive Fibonacci script. This showed that the model sometimes provides additional best-practice advice beyond what is explicitly requested.