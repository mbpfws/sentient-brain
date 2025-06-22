// Sample TypeScript file to test parser integration
import { FastAPI } from 'fastapi';
import * as React from 'react';

interface User {
  id: number;
  name: string;
  email: string;
}

class UserService {
  private apiUrl: string;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }

  async getUser(id: number): Promise<User> {
    const response = await fetch(`${this.apiUrl}/users/${id}`);
    return response.json();
  }

  createUser(userData: Omit<User, 'id'>): Promise<User> {
    return fetch(`${this.apiUrl}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    }).then(res => res.json());
  }
}

export function processUsers(users: User[]): User[] {
  return users.filter(user => user.email.includes('@'))
               .sort((a, b) => a.name.localeCompare(b.name));
}

const createValidator = (pattern: RegExp) => (value: string) => pattern.test(value);

export default UserService; 