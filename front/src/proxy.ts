import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Rutas protegidas para administradores
  const adminRoutes = ['/dashboard/admin'];
  
  // Rutas protegidas para clientes
  const clientRoutes = ['/dashboard/client'];

  // Verificar si la ruta actual es una ruta protegida
  const isAdminRoute = adminRoutes.some(route => pathname.startsWith(route));
  const isClientRoute = clientRoutes.some(route => pathname.startsWith(route));

  // Si es una ruta protegida, verificar autenticación
  if (isAdminRoute || isClientRoute) {
    // Obtener el token y usuario del localStorage usando cookies como alternativa
    // Ya que no podemos acceder directamente a localStorage en el proxy
    const token = request.cookies.get('access_token')?.value;
    const userCookie = request.cookies.get('user')?.value;

    // Si no hay token, redirigir al login
    if (!token || !userCookie) {
      const url = request.nextUrl.clone();
      url.pathname = '/auth/login';
      return NextResponse.redirect(url);
    }

    try {
      const user = JSON.parse(userCookie);

      // Verificar que el usuario tenga el rol correcto
      if (isAdminRoute && user.role !== 'ADMIN') {
        const url = request.nextUrl.clone();
        url.pathname = '/dashboard/client';
        return NextResponse.redirect(url);
      }

      if (isClientRoute && user.role !== 'CLIENT') {
        const url = request.nextUrl.clone();
        url.pathname = '/dashboard/admin';
        return NextResponse.redirect(url);
      }
    } catch (error) {
      // Si hay error al parsear el usuario, redirigir al login
      const url = request.nextUrl.clone();
      url.pathname = '/auth/login';
      return NextResponse.redirect(url);
    }
  }

  return NextResponse.next();
}

// Configurar las rutas que el proxy debe procesar
export const config = {
  matcher: [
    '/dashboard/admin/:path*',
    '/dashboard/client/:path*',
  ],
};
