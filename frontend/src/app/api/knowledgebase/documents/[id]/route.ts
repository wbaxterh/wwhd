import { NextRequest } from 'next/server';

export const dynamic = 'force-dynamic';

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authHeader = request.headers.get('authorization');
  const body = await request.json();
  const { id } = await params;

  const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/${id}`, {
    method: 'PUT',
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authHeader = request.headers.get('authorization');
  const { id } = await params;

  const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com'}/api/v1/documents/${id}`, {
    method: 'DELETE',
    headers: {
      ...(authHeader && { 'Authorization': authHeader }),
    },
  });

  if (backendResponse.status === 204 || backendResponse.status === 200) {
    return Response.json({ message: 'Document deleted successfully' }, {
      status: 200,
    });
  }

  const data = await backendResponse.json();
  return Response.json(data, {
    status: backendResponse.status,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}