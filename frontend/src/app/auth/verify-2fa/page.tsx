'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { verify2FA } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

function Verify2FAContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Focus en el primer input al cargar
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string) => {
    // Solo permitir números
    if (value && !/^\d$/.test(value)) {
      return;
    }

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    setError('');

    // Auto-focus al siguiente input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    // Retroceder al input anterior con Backspace
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    
    if (pastedData) {
      const newCode = pastedData.split('').concat(Array(6 - pastedData.length).fill(''));
      setCode(newCode);
      
      // Focus en el siguiente input vacío o el último
      const nextEmptyIndex = pastedData.length < 6 ? pastedData.length : 5;
      inputRefs.current[nextEmptyIndex]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    const totpCode = code.join('');

    if (totpCode.length !== 6) {
      setError('El código debe tener 6 dígitos');
      return;
    }

    const email = searchParams.get('email');
    const password = searchParams.get('password');

    if (!email || !password) {
      setError('Faltan credenciales. Por favor, regístrate nuevamente.');
      return;
    }

    setIsLoading(true);

    try {
      await verify2FA({
        request: {
          email,
          password,
        },
        totp_request: {
          totp_code: totpCode,
        },
      });

      // Redirigir al login después de la verificación exitosa
      router.push('/auth/login');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Código incorrecto. Inténtalo de nuevo.');
      setCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Verificar Código 2FA</CardTitle>
          <CardDescription>
            Ingresa el código de 6 dígitos de Microsoft Authenticator
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="code-0" className="text-center block">
                Código de Verificación
              </Label>
              <div className="flex gap-2 justify-center" onPaste={handlePaste}>
                {code.map((digit, index) => (
                  <Input
                    key={index}
                    id={`code-${index}`}
                    ref={(el) => {
                      inputRefs.current[index] = el;
                    }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    className="w-12 h-12 text-center text-lg font-semibold"
                    disabled={isLoading}
                    aria-label={`Dígito ${index + 1} del código`}
                    required
                  />
                ))}
              </div>
              <p className="text-xs text-muted-foreground text-center mt-2">
                Abre Microsoft Authenticator y busca el código de 6 dígitos
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm" role="alert">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading || code.some(d => !d)}
              >
                {isLoading ? 'Verificando...' : 'Verificar Código'}
              </Button>

              <Button 
                type="button" 
                variant="outline" 
                className="w-full" 
                onClick={() => router.push('/auth/register')}
                disabled={isLoading}
              >
                Volver al Registro
              </Button>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm text-blue-800">
                <strong>Nota:</strong> Los códigos cambian cada 30 segundos. Si tu código expira, espera a que aparezca uno nuevo en la aplicación.
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function Verify2FAPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    }>
      <Verify2FAContent />
    </Suspense>
  );
}
