import client from '../client';
import type {
    InstrumentSchema,
    InstrumentCreate,
    FootprintCCDSchema,
    FootprintCCDCreate,
    InstrumentFilters
} from '../types/instrument.types';

export const instrumentService = {
    getInstruments: async (filters?: InstrumentFilters): Promise<InstrumentSchema[]> => {
        const response = await client.get<InstrumentSchema[]>('/api/v1/instruments', { params: filters });
        return response.data;
    },

    getReportingInstruments: async (): Promise<InstrumentSchema[]> => {
        const response = await client.get<InstrumentSchema[]>('/api/v1/instruments', { params: { reporting_only: true } });
        return response.data;
    },

    createInstrument: async (instrument: InstrumentCreate): Promise<InstrumentSchema> => {
        const response = await client.post<InstrumentSchema>('/api/v1/instruments', instrument);
        return response.data;
    },

    getFootprints: async (id?: number, name?: string): Promise<FootprintCCDSchema[]> => {
        const response = await client.get<FootprintCCDSchema[]>('/api/v1/footprints', { params: { id, name } });
        return response.data;
    },

    createFootprint: async (footprint: FootprintCCDCreate): Promise<FootprintCCDSchema> => {
        const response = await client.post<FootprintCCDSchema>('/api/v1/footprints', footprint);
        return response.data;
    }
};
