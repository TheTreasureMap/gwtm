export interface ApiKeyAuth {
	api_token: string;
}

export interface ApiResponse<T> {
	data?: T;
	message?: string;
	errors?: any[];
	warnings?: any[];
}

export interface HealthResponse {
	status: string;
	timestamp?: string;
}

export interface ServiceStatusResponse {
	database: 'connected' | 'disconnected';
	redis: 'connected' | 'disconnected';
	details?: Record<string, any>;
}
