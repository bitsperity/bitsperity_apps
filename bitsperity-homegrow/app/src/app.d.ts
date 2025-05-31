// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			mqtt: {
				isConnected: () => boolean;
				getStatus: () => any;
				sendCommand: (deviceId: string, command: any) => Promise<boolean>;
			};
		}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
