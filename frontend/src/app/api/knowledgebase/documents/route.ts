import { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('authorization');
  const { searchParams } = new URL(request.url);

  const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/?${searchParams}`, {
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

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('authorization');
  const body = await request.json();

  const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(authHeader && { 'Authorization': authHeader }),
    },
    body: JSON.stringify(body),
  });

  const data = await backendResponse.json();

  return Response.json(data, {
    status: backendResponse.status,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}