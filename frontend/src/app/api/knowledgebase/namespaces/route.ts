import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('authorization');

  const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/namespaces`, {
    method: 'GET',
    headers: {
      ...(authHeader && { 'Authorization': authHeader }),
    },
  });

  const data = await backendResponse.json();

  return Response.json(data, {
    status: backendResponse.status,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}