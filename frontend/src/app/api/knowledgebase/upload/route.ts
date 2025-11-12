import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('authorization');
  const formData = await request.formData();

  const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/upload`, {
    method: 'POST',
    headers: {
      ...(authHeader && { 'Authorization': authHeader }),
    },
    body: formData,
  });

  const data = await backendResponse.json();

  return Response.json(data, {
    status: backendResponse.status,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}