"use client";

// Hook di autenticazione docente (Firebase Auth, email/password).

import { useEffect, useState } from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from "firebase/auth";
import { auth } from "@/lib/firebase";

export interface UseAuth {
  // Utente autenticato, null se non loggato
  user: User | null;
  // True finché non si conosce lo stato di autenticazione iniziale
  loading: boolean;
  // Esegue il login con email e password
  login: (email: string, password: string) => Promise<void>;
  // Esegue il logout
  logout: () => Promise<void>;
}

export function useAuth(): UseAuth {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Sottoscrizione ai cambi di stato dell'autenticazione
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  async function login(email: string, password: string): Promise<void> {
    await signInWithEmailAndPassword(auth, email, password);
  }

  async function logout(): Promise<void> {
    await signOut(auth);
  }

  return { user, loading, login, logout };
}
