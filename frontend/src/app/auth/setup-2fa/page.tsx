'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { QRCodeSVG } from 'qrcode.react';
import { setup2FA } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

function Setup2FAContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [qrUri, setQrUri] = useState('');
  const [secret, setSecret] = useState('');
  const [manualKey, setManualKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [hasQR, setHasQR] = useState(false);

  useEffect(() => {
    const emailParam = searchParams.get('email');
    const passwordParam = searchParams.get('password');

    if (!emailParam || !passwordParam) {
      // No hay credenciales en la URL, mostrar formulario
      setShowForm(true);
      return;
    }

    // Hay credenciales en la URL, cargar QR automáticamente
    setEmail(emailParam);
    setPassword(passwordParam);
    fetchQRCode(emailParam, passwordParam);
  }, [searchParams]);

  const fetchQRCode = async (emailValue: string, passwordValue: string) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await setup2FA({ email: emailValue, password: passwordValue });
      setQrUri(response.qr_uri);
      setSecret(response.secret);
      setManualKey(response.manual_entry_key);
      setHasQR(true);
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al obtener el código QR');
      setShowForm(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!email || !password) {
      setError('El correo electrónico y la contraseña son obligatorios');
      return;
    }

    await fetchQRCode(email, password);
  };

  const handleCopyKey = async () => {
    try {
      await navigator.clipboard.writeText(manualKey);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Error al copiar:', err);
    }
  };

  const handleContinue = () => {
    router.push(
      `/auth/verify-2fa?email=${encodeURIComponent(email || '')}&password=${encodeURIComponent(password || '')}`
    );
  };

  // Mostrar formulario de entrada de credenciales
  if (showForm && !hasQR) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold">Configurar Autenticación 2FA</CardTitle>
            <CardDescription>
              Ingresa tus credenciales para configurar la autenticación de dos factores
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
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
                  autoComplete="current-password"
                  className="w-full"
                  disabled={isLoading}
                />
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? 'Generando código QR...' : 'Generar Código QR'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
        <Card className="w-full max-w-md shadow-xl">
          <CardContent className="p-8">
            <div className="flex flex-col items-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              <p className="text-muted-foreground">Generando código QR...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && hasQR) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-red-800">{error}</p>
            <div className="flex gap-2">
              <Button onClick={() => {
                setShowForm(true);
                setHasQR(false);
                setError('');
              }} className="flex-1" variant="outline">
                Intentar de nuevo
              </Button>
              <Button onClick={() => router.push('/auth/register')} className="flex-1">
                Volver al Registro
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <Card className="w-full max-w-lg shadow-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Configurar Autenticación 2FA</CardTitle>
          <CardDescription>
            Escanea el código QR con Microsoft Authenticator para completar tu registro
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="text-sm space-y-2">
              <p className="font-semibold">Instrucciones:</p>
              <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                <li>Descarga Microsoft Authenticator en tu dispositivo móvil</li>
                <li>Abre la aplicación y pulsa "Añadir cuenta"</li>
                <li>Selecciona "Otra cuenta (Google, Facebook, etc.)"</li>
                <li>Escanea el código QR que aparece abajo</li>
              </ol>
            </div>

            <Separator />

            <div className="flex flex-col items-center space-y-4">
              <div
                className="bg-white p-4 rounded-lg border-2 border-gray-200 shadow-sm"
                role="img"
                aria-label={`Código QR para configurar autenticación de dos factores. Si no puedes escanearlo, usa la clave manual: ${manualKey}`}
              >
                {qrUri && (
                  <QRCodeSVG
                    value={qrUri}
                    size={200}
                    level="H"
                    includeMargin={true}
                  />
                )}
              </div>

              <div className="w-full">
                <p className="text-sm font-medium mb-2">
                  ¿No puedes escanear el código?
                </p>
                <p className="text-xs text-muted-foreground mb-2">
                  Introduce esta clave manualmente en Microsoft Authenticator:
                </p>
                <div className="flex items-center space-x-2">
                  <code className="flex-1 p-3 bg-gray-100 rounded text-sm font-mono break-all">
                    {manualKey}
                  </code>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCopyKey}
                    aria-label="Copiar clave manual"
                  >
                    {copySuccess ? '✓ Copiado' : 'Copiar'}
                  </Button>
                </div>
              </div>
            </div>

            <Separator />

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm text-blue-800">
                <strong>Importante:</strong> Guarda esta clave en un lugar seguro. La necesitarás si pierdes el acceso a tu dispositivo.
              </p>
            </div>

            <Button
              onClick={handleContinue}
              className="w-full"
              size="lg"
            >
              Continuar a Verificación
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function Setup2FAPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    }>
      <Setup2FAContent />
    </Suspense>
  );
}
