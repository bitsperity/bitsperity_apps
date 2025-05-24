import bcrypt from 'bcrypt';
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';

// Validation schemas
const LoginSchema = z.object({
  username: z.string().min(1, 'Benutzername ist erforderlich'),
  password: z.string().min(1, 'Passwort ist erforderlich')
});

const RegisterSchema = z.object({
  username: z.string().min(3, 'Benutzername muss mindestens 3 Zeichen haben').max(50),
  password: z.string().min(6, 'Passwort muss mindestens 6 Zeichen haben'),
  email: z.string().email('Ungültige E-Mail-Adresse').optional()
});

export default async function authRoutes(fastify, options) {
  
  // Login endpoint
  fastify.post('/login', {
    schema: {
      body: zodToJsonSchema(LoginSchema)
    }
  }, async (request, reply) => {
    try {
      const { username, password } = request.body;

      // Find user in database
      const user = await fastify.db.collection('users').findOne({ username });
      
      if (!user) {
        return reply.status(401).send({ 
          error: 'Ungültige Anmeldedaten',
          message: 'Benutzername oder Passwort ist falsch'
        });
      }

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password);
      
      if (!isValidPassword) {
        return reply.status(401).send({ 
          error: 'Ungültige Anmeldedaten',
          message: 'Benutzername oder Passwort ist falsch'
        });
      }

      // Generate JWT token
      const token = await reply.jwtSign(
        { 
          userId: user._id, 
          username: user.username 
        },
        { 
          expiresIn: '24h' 
        }
      );

      // Update last login
      await fastify.db.collection('users').updateOne(
        { _id: user._id },
        { 
          $set: { 
            lastLogin: new Date(),
            lastLoginIP: request.ip
          } 
        }
      );

      return {
        token,
        user: {
          id: user._id,
          username: user.username,
          email: user.email,
          createdAt: user.createdAt,
          lastLogin: new Date()
        }
      };

    } catch (error) {
      fastify.log.error('Login error:', error);
      reply.status(500).send({ 
        error: 'Anmeldefehler',
        message: 'Ein Fehler ist bei der Anmeldung aufgetreten'
      });
    }
  });

  // Register endpoint (nur wenn keine Benutzer existieren)
  fastify.post('/register', {
    schema: {
      body: zodToJsonSchema(RegisterSchema)
    }
  }, async (request, reply) => {
    try {
      // Check if any users exist (nur ersten Admin-User erlauben)
      const userCount = await fastify.db.collection('users').countDocuments();
      
      if (userCount > 0) {
        return reply.status(403).send({ 
          error: 'Registrierung nicht erlaubt',
          message: 'Es existiert bereits ein Benutzer. Kontaktieren Sie den Administrator.'
        });
      }

      const { username, password, email } = request.body;

      // Check if username already exists
      const existingUser = await fastify.db.collection('users').findOne({ username });
      
      if (existingUser) {
        return reply.status(409).send({ 
          error: 'Benutzername bereits vergeben',
          message: 'Dieser Benutzername ist bereits registriert'
        });
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(password, 12);

      // Create user
      const newUser = {
        username,
        password: hashedPassword,
        email: email || null,
        role: 'admin', // Erster Benutzer ist immer Admin
        createdAt: new Date(),
        updatedAt: new Date(),
        isActive: true
      };

      const result = await fastify.db.collection('users').insertOne(newUser);

      // Generate JWT token
      const token = await reply.jwtSign(
        { 
          userId: result.insertedId, 
          username: newUser.username 
        },
        { 
          expiresIn: '24h' 
        }
      );

      return {
        token,
        user: {
          id: result.insertedId,
          username: newUser.username,
          email: newUser.email,
          role: newUser.role,
          createdAt: newUser.createdAt
        }
      };

    } catch (error) {
      fastify.log.error('Registration error:', error);
      reply.status(500).send({ 
        error: 'Registrierungsfehler',
        message: 'Ein Fehler ist bei der Registrierung aufgetreten'
      });
    }
  });

  // Logout endpoint
  fastify.post('/logout', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      // In einer echten Anwendung würde man hier das Token invalidieren
      // Da JWT stateless ist, loggen wir nur den Logout
      fastify.log.info(`User ${request.user.username} logged out`);
      
      return { message: 'Erfolgreich abgemeldet' };
    } catch (error) {
      fastify.log.error('Logout error:', error);
      reply.status(500).send({ 
        error: 'Abmeldefehler',
        message: 'Ein Fehler ist bei der Abmeldung aufgetreten'
      });
    }
  });

  // Token refresh endpoint
  fastify.post('/refresh', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      // Generate new token
      const token = await reply.jwtSign(
        { 
          userId: request.user.userId, 
          username: request.user.username 
        },
        { 
          expiresIn: '24h' 
        }
      );

      return { token };
    } catch (error) {
      fastify.log.error('Token refresh error:', error);
      reply.status(500).send({ 
        error: 'Token-Aktualisierungsfehler',
        message: 'Token konnte nicht aktualisiert werden'
      });
    }
  });

  // Get current user profile
  fastify.get('/profile', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    try {
      const user = await fastify.db.collection('users').findOne(
        { _id: request.user.userId },
        { projection: { password: 0 } }
      );

      if (!user) {
        return reply.status(404).send({ 
          error: 'Benutzer nicht gefunden',
          message: 'Benutzerprofil konnte nicht geladen werden'
        });
      }

      return {
        user: {
          id: user._id,
          username: user.username,
          email: user.email,
          role: user.role,
          createdAt: user.createdAt,
          lastLogin: user.lastLogin,
          isActive: user.isActive
        }
      };
    } catch (error) {
      fastify.log.error('Profile fetch error:', error);
      reply.status(500).send({ 
        error: 'Profil-Ladefehler',
        message: 'Benutzerprofil konnte nicht geladen werden'
      });
    }
  });

  // Update user profile
  fastify.put('/profile', {
    preHandler: [fastify.authenticate],
    schema: {
      body: zodToJsonSchema(z.object({
        email: z.string().email().optional(),
        currentPassword: z.string().optional(),
        newPassword: z.string().min(6).optional()
      }))
    }
  }, async (request, reply) => {
    try {
      const { email, currentPassword, newPassword } = request.body;
      const updateData = {};

      // Update email if provided
      if (email) {
        updateData.email = email;
      }

      // Change password if provided
      if (newPassword && currentPassword) {
        const user = await fastify.db.collection('users').findOne({ _id: request.user.userId });
        
        const isValidPassword = await bcrypt.compare(currentPassword, user.password);
        if (!isValidPassword) {
          return reply.status(400).send({ 
            error: 'Falsches Passwort',
            message: 'Das aktuelle Passwort ist falsch'
          });
        }

        updateData.password = await bcrypt.hash(newPassword, 12);
      }

      if (Object.keys(updateData).length > 0) {
        updateData.updatedAt = new Date();
        
        await fastify.db.collection('users').updateOne(
          { _id: request.user.userId },
          { $set: updateData }
        );
      }

      return { message: 'Profil erfolgreich aktualisiert' };
    } catch (error) {
      fastify.log.error('Profile update error:', error);
      reply.status(500).send({ 
        error: 'Profil-Aktualisierungsfehler',
        message: 'Profil konnte nicht aktualisiert werden'
      });
    }
  });

  // Check auth status
  fastify.get('/status', {
    preHandler: [fastify.authenticate]
  }, async (request, reply) => {
    return { 
      authenticated: true,
      user: {
        id: request.user.userId,
        username: request.user.username
      }
    };
  });
} 