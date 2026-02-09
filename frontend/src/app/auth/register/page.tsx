'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { register } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function UnifiedRegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    // Validaciones del lado del cliente
    if (!email || !password || !confirmPassword || !name) {
      setError('Revise los campos que son obligatorios');
      return;
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    // Validación básica del teléfono
    if (phoneNumber != '') {
      if (phoneNumber.length < 10) {
        setError('El número de teléfono debe tener al menos 10 dígitos');
        return;
      }
      return;
    }


    setIsLoading(true);

    try {
      await register({
        email,
        password,
        name,
        phone_number: phoneNumber,
      });

      // Redirigir a la configuración de 2FA pasando las credenciales
      router.push(
        `/auth/setup-2fa?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al registrar el usuario');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Registro de Usuario</CardTitle>
          <CardDescription>
            Crea tu cuenta para acceder al sistema. Después deberás configurar la autenticación de dos factores.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm" role="alert">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="name">
                Nombre Completo <span className="text-red-500" aria-label="requerido">*</span>
              </Label>
              <Input
                id="name"
                name="name"
                type="text"
                placeholder="Juan Pérez"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                aria-required="true"
                className="w-full"
                disabled={isLoading}
                autoComplete="name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">
                Teléfono
              </Label>
              <Input
                id="phone"
                name="phone"
                type="tel"
                placeholder="+593600123456"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                aria-required="false"
                className="w-full"
                disabled={isLoading}
                autoComplete="tel"
              />
              <p className="text-sm text-gray-500">
                Incluye el código de país (ej: +593 para Ecuador)
              </p>
            </div>

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
                autoComplete="new-password"
                className="w-full"
                disabled={isLoading}
              />
              <p className="text-sm text-gray-500">
                Mínimo 8 caracteres
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">
                Confirmar Contraseña <span className="text-red-500" aria-label="requerido">*</span>
              </Label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                aria-required="true"
                autoComplete="new-password"
                className="w-full"
                disabled={isLoading}
              />
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
            >
              {isLoading ? 'Registrando...' : 'Registrarse'}
            </Button>

            <div className="text-center text-sm text-gray-600 mt-4">
              ¿Ya tienes una cuenta?{' '}
              <Link href="/auth/login" className="text-blue-600 hover:underline font-medium">
                Inicia sesión aquí
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
