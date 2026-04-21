import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, setAuthToken } from '../utils/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const initAuth = async () => {
            const storedToken = localStorage.getItem('tf_token');
            if (storedToken) {
                setAuthToken(storedToken);
                try {
                    const data = await api.getMe();
                    setUser(data);
                } catch (e) {
                    localStorage.removeItem('tf_token');
                    setAuthToken(null);
                }
            }
            setLoading(false);
        };
        initAuth();

        const handleUnauthorized = () => {
            setUser(null);
            localStorage.removeItem('tf_token');
            setAuthToken(null);
        };

        window.addEventListener('auth-unauthorized', handleUnauthorized);
        return () => window.removeEventListener('auth-unauthorized', handleUnauthorized);
    }, []);

    const login = async (email, password) => {
        const data = await api.login(email, password);
        localStorage.setItem('tf_token', data.token);
        setAuthToken(data.token);
        setUser(data.user);
        return data;
    };

    const signup = async (email, password) => {
        const data = await api.signup(email, password);
        localStorage.setItem('tf_token', data.token);
        setAuthToken(data.token);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        localStorage.removeItem('tf_token');
        setAuthToken(null);
        setUser(null);
    };

    const loginWithGoogle = async (data) => {
        // data = { access_token, is_new_user, user: { email, name } }
        localStorage.setItem('tf_token', data.access_token);
        setAuthToken(data.access_token);
        try {
            const me = await api.getMe();
            setUser(me);
        } catch {
            setUser(data.user);
        }
        return data;
    };

    const refreshUser = async () => {
        try {
            const me = await api.getMe();
            setUser(me);
            return me;
        } catch (e) {
            // ignore
        }
    };

    const updateName = async (name) => {
        await api.updateName(name);
        setUser((prev) => ({ ...prev, name }));
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, signup, logout, loginWithGoogle, refreshUser, updateName }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
