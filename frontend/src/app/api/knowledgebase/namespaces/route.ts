import { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('authorization');

  try {
    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/namespaces`, {
      method: 'GET',
      headers: {
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    if (!backendResponse.ok) {
      return Response.json({ error: 'Backend request failed' }, { status: backendResponse.status });
    }

    const data = await backendResponse.json();

    return Response.json(data, {
      status: backendResponse.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('API Route Error:', error);
    return Response.json({ error: 'Backend connection failed' }, { status: 500 });
  }
}