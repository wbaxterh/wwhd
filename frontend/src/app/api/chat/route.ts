export const runtime = 'edge';

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1];
  const authHeader = req.headers.get('authorization');

  try {
    // Connect directly to backend - no fallbacks
    console.log('Connecting to backend:', `${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/chat/stream`);

    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
      body: JSON.stringify({
        content: lastMessage.content,
        chat_id: null
      })
    });

    console.log('Backend response status:', backendResponse.status);

    if (!backendResponse.ok) {
      throw new Error(`Backend returned ${backendResponse.status}: ${backendResponse.statusText}`);
    }

    if (!backendResponse.body) {
      throw new Error('No response body from backend');
    }

    // Stream the response from backend
    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      async start(controller) {
        const reader = backendResponse.body!.getReader();

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = new TextDecoder().decode(value);
            console.log('Backend chunk:', chunk);

            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6).trim();

                if (data === '' || data === 'null') continue;

                try {
                  const parsed = JSON.parse(data);

                  if (parsed.type === 'token' && parsed.content) {
                    // Convert to OpenAI-style format for frontend compatibility
                    const formatted = {
                      choices: [{
                        delta: { content: parsed.content }
                      }]
                    };
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify(formatted)}\n\n`));
                  } else if (parsed.type === 'done') {
                    controller.enqueue(encoder.encode('data: [DONE]\n\n'));
                  }
                } catch (e) {
                  console.error('Error parsing backend JSON:', e, 'Data:', data);
                }
              }
            }
          }
        } catch (error) {
          console.error('Error reading from backend:', error);
          throw error;
        } finally {
          reader.releaseLock();
        }

        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      }
    });

    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });

  } catch (error) {
    console.error('Backend connection failed:', error);

    // Return proper error response instead of fallback
    return new Response(
      JSON.stringify({
        error: 'Backend unavailable',
        message: 'Unable to connect to Herman. Please try again later.',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
  }
}