'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';
import axios from 'axios';

export default function UnifiedLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [error, setError] = useState('');
  const [isBlocked, setIsBlocked] = useState(false);
  const [blockMessage, setBlockMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setIsBlocked(false);
    setBlockMessage('');

    // Validaciones del lado del cliente
    if (!email || !password || !totpCode) {
      setError('Todos los campos son obligatorios');
      return;
    }

    if (totpCode.length !== 6 || !/^\d{6}$/.test(totpCode)) {
      setError('El código 2FA debe tener 6 dígitos');
      return;
    }

    setIsLoading(true);

    try {
      const response = await login({
        email,
        password,
        totp_code: totpCode,
      });

      // Guardar el token en localStorage
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      // También guardar en cookies para el middleware
      document.cookie = `access_token=${response.access_token}; path=/; max-age=86400; SameSite=Strict`;
      document.cookie = `user=${encodeURIComponent(JSON.stringify(response.user))}; path=/; max-age=86400; SameSite=Strict`;

      // Redirigir según el rol del usuario
      if (response.user.role === 'ADMIN') {
        router.push('/dashboard/admin');
      } else if (response.user.role === 'CLIENT') {
        router.push('/dashboard/client');
      } else {
        setError('Rol de usuario desconocido');
        setIsLoading(false);
      }
    } catch (err) {
      setIsLoading(false);

      // Verificar si es un error de bloqueo (403)
      if (axios.isAxiosError(err) && err.response?.status === 403) {
        const detail = err.response?.data?.detail;
        setIsBlocked(true);
        setBlockMessage(detail || 'Cuenta bloqueada temporalmente por seguridad. Intenta nuevamente en unos minutos.');
      } else {
        setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Iniciar Sesión</CardTitle>
          <CardDescription>
            Ingresa tus credenciales y el código de Microsoft Authenticator
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Alerta de bloqueo */}
            {isBlocked && blockMessage && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md" role="alert">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="font-semibold text-sm">{blockMessage}</p>
                </div>
              </div>
            )}

            {/* Alerta de error general */}
            {error && !isBlocked && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm" role="alert">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">
                Correo Electrónico <span className="text-red-500" aria-label="requerido">*</span>
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="tu-email@ejemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                aria-required="true"
                aria-invalid={error.includes('email') ? 'true' : 'false'}
                autoComplete="email"
                className="w-full"
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">
                Contraseña <span className="text-red-500" aria-label="requerido">*</span>
              </Label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                aria-required="true"
                aria-invalid={error.includes('contraseña') ? 'true' : 'false'}
                autoComplete="current-password"
                className="w-full"
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="totp">
                Código 2FA <span className="text-red-500" aria-label="requerido">*</span>
              </Label>
              <Input
                id="totp"
                name="totp"
                type="text"
                placeholder="123456"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                required
                aria-required="true"
                aria-invalid={error.includes('2FA') ? 'true' : 'false'}
                autoComplete="one-time-code"
                className="w-full"
                disabled={isLoading}
                maxLength={6}
                pattern="\d{6}"
              />
              <p className="text-sm text-gray-500">
                Ingresa el código de 6 dígitos desde Microsoft Authenticator
              </p>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
            >
              {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </Button>

            <div className="text-center text-sm text-gray-600 mt-4">
              ¿No tienes una cuenta?{' '}
              <Link href="/auth/register" className="text-blue-600 hover:underline font-medium">
                Regístrate aquí
              </Link>
            </div>

            <div className="text-center text-sm text-gray-600">
              ¿Aún no estás autenticado?{' '}
              <Link href="/auth/setup-2fa" className="text-blue-600 hover:underline font-medium">
                Hazlo aquí
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
