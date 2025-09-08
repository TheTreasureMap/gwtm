import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
	fetchSunMoonPositions,
	convertToMJD,
	getDefaultSunMoonPositions,
	type SunMoonData
} from '../astronomicalCalculations';
import {
	mockDate,
	createMockFetchResponse,
	expectApproximatelyEqual
} from '../../../test-utils/helpers';

// Tests for astronomical calculation utilities including MJD conversion and sun/moon positioning
describe('Astronomical Calculations', () => {
	let mockDateHelper: { mockDate: Date; restore: () => void };

	beforeEach(() => {
		// Mock a consistent date for testing
		mockDateHelper = mockDate('2024-01-01T12:00:00.000Z');
		vi.clearAllMocks();
	});

	afterEach(() => {
		mockDateHelper.restore();
		vi.restoreAllMocks();
	});

	// Modified Julian Date conversion
	describe('convertToMJD', () => {
		it('should convert Unix epoch to correct MJD', () => {
			const unixEpoch = new Date('1970-01-01T00:00:00.000Z');
			const mjd = convertToMJD(unixEpoch);
			// Unix epoch (1970-01-01) corresponds to MJD 40587
			expectApproximatelyEqual(mjd, 40587.0);
		});

		it('should convert known dates to correct MJD', () => {
			// Test date: 2024-01-01T12:00:00.000Z
			const testDate = new Date('2024-01-01T12:00:00.000Z');
			const mjd = convertToMJD(testDate);
			// MJD for 2024-01-01 12:00 UTC should be around 60310.5
			expectApproximatelyEqual(mjd, 60310.5, 0.1);
		});

		it('should handle fractional days correctly', () => {
			// Test different times of day
			const midnight = new Date('2024-01-01T00:00:00.000Z');
			const noon = new Date('2024-01-01T12:00:00.000Z');

			const mjdMidnight = convertToMJD(midnight);
			const mjdNoon = convertToMJD(noon);

			// Noon should be 0.5 days after midnight
			expectApproximatelyEqual(mjdNoon - mjdMidnight, 0.5);
		});

		it('should round to 3 decimal places', () => {
			const testDate = new Date('2024-01-01T12:34:56.789Z');
			const mjd = convertToMJD(testDate);

			// Check that result has at most 3 decimal places
			const decimals = mjd.toString().split('.')[1]?.length || 0;
			expect(decimals).toBeLessThanOrEqual(3);
		});

		it('should handle dates before Unix epoch', () => {
			const testDate = new Date('1950-01-01T00:00:00.000Z');
			const mjd = convertToMJD(testDate);

			// Should be a positive MJD (around 33282)
			expect(mjd).toBeGreaterThan(0);
			expectApproximatelyEqual(mjd, 33282, 1);
		});

		it('should handle future dates', () => {
			const testDate = new Date('2050-01-01T00:00:00.000Z');
			const mjd = convertToMJD(testDate);

			// Should be a reasonable MJD for 2050 (approximately 69807)
			expect(mjd).toBeGreaterThanOrEqual(69807); // MJD for 2050-01-01
		});
	});

	// Default fallback positions
	describe('getDefaultSunMoonPositions', () => {
		it('should return expected default positions', () => {
			const defaults = getDefaultSunMoonPositions();

			expect(defaults).toEqual({
				sun_ra: 180.0,
				sun_dec: 0.0,
				moon_ra: 270.0,
				moon_dec: 10.0
			});
		});

		it('should return consistent values across calls', () => {
			const defaults1 = getDefaultSunMoonPositions();
			const defaults2 = getDefaultSunMoonPositions();

			expect(defaults1).toEqual(defaults2);
		});
	});

	// API fetching with fallback calculations
	describe('fetchSunMoonPositions', () => {
		beforeEach(() => {
			global.fetch = vi.fn();
		});

		it('should return null for empty time signal', async () => {
			const result = await fetchSunMoonPositions('');
			expect(result).toBeNull();

			const result2 = await fetchSunMoonPositions(null as any);
			expect(result2).toBeNull();
		});

		it('should successfully fetch from API when available', async () => {
			const mockResponse = {
				sun_ra: 123.45,
				sun_dec: -23.5,
				moon_ra: 234.56,
				moon_dec: 15.2
			};

			(global.fetch as any).mockResolvedValue(createMockFetchResponse(mockResponse));

			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			expect(result).toEqual(mockResponse);
			expect(fetch).toHaveBeenCalledWith(
				'http://localhost:8000/temp_sun_moon_positions?time_of_signal=2024-01-01T12%3A00%3A00.000Z'
			);
		});

		it('should handle API errors gracefully', async () => {
			(global.fetch as any).mockRejectedValue(new Error('Network error'));

			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			// Should fall back to approximate calculations
			expect(result).not.toBeNull();
			expect(result).toHaveProperty('sun_ra');
			expect(result).toHaveProperty('sun_dec');
			expect(result).toHaveProperty('moon_ra');
			expect(result).toHaveProperty('moon_dec');
		});

		it('should handle HTTP error responses', async () => {
			(global.fetch as any).mockResolvedValue({
				ok: false,
				status: 500,
				statusText: 'Internal Server Error',
				json: () => Promise.resolve({ error: 'Server error' })
			});

			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			// Should fall back to approximate calculations
			expect(result).not.toBeNull();
			expect(typeof result?.sun_ra).toBe('number');
		});

		it('should encode URL parameters correctly', async () => {
			const mockResponse = { sun_ra: 0, sun_dec: 0, moon_ra: 0, moon_dec: 0 };
			(global.fetch as any).mockResolvedValue(createMockFetchResponse(mockResponse));

			const timeWithSpecialChars = '2024-01-01T12:00:00+05:30';
			await fetchSunMoonPositions(timeWithSpecialChars);

			expect(fetch).toHaveBeenCalledWith(
				'http://localhost:8000/temp_sun_moon_positions?time_of_signal=2024-01-01T12%3A00%3A00%2B05%3A30'
			);
		});
	});

	// Offline calculation algorithms
	describe('Fallback sun/moon calculations', () => {
		beforeEach(() => {
			// Mock fetch to always fail so we test the fallback
			global.fetch = vi.fn().mockRejectedValue(new Error('No network'));
		});

		it('should calculate approximate positions for different dates', async () => {
			const springEquinox = await fetchSunMoonPositions('2024-03-20T12:00:00.000Z');
			const summerSolstice = await fetchSunMoonPositions('2024-06-21T12:00:00.000Z');
			const winterSolstice = await fetchSunMoonPositions('2024-12-21T12:00:00.000Z');

			// Verify all results are returned
			expect(springEquinox).not.toBeNull();
			expect(summerSolstice).not.toBeNull();
			expect(winterSolstice).not.toBeNull();

			// Check that positions vary with season (different declinations)
			expect(springEquinox!.sun_dec).not.toEqual(summerSolstice!.sun_dec);
			expect(summerSolstice!.sun_dec).not.toEqual(winterSolstice!.sun_dec);

			// Summer solstice should have positive declination
			expect(summerSolstice!.sun_dec).toBeGreaterThan(0);

			// Winter solstice should have negative declination
			expect(winterSolstice!.sun_dec).toBeLessThan(0);
		});

		it('should calculate reasonable sun positions', async () => {
			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			expect(result).not.toBeNull();

			// Sun RA should be in valid range [0, 360)
			expect(result!.sun_ra).toBeGreaterThanOrEqual(0);
			expect(result!.sun_ra).toBeLessThan(360);

			// Sun declination should be in valid range [-90, 90]
			expect(result!.sun_dec).toBeGreaterThanOrEqual(-90);
			expect(result!.sun_dec).toBeLessThanOrEqual(90);

			// For January 1st, sun should be near winter solstice position
			// (around Dec 21), so declination should be negative
			expect(result!.sun_dec).toBeLessThan(0);
		});

		it('should calculate moon positions offset from sun', async () => {
			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			expect(result).not.toBeNull();

			// Moon RA should be in valid range [0, 360)
			expect(result!.moon_ra).toBeGreaterThanOrEqual(0);
			expect(result!.moon_ra).toBeLessThan(360);

			// Moon declination should be in valid range [-90, 90]
			expect(result!.moon_dec).toBeGreaterThanOrEqual(-90);
			expect(result!.moon_dec).toBeLessThanOrEqual(90);

			// Moon RA should be roughly 90 degrees offset from sun
			const expectedMoonRA = (result!.sun_ra + 90) % 360;
			expectApproximatelyEqual(result!.moon_ra, expectedMoonRA, 1);
		});

		it('should handle different years correctly', async () => {
			const year2023 = await fetchSunMoonPositions('2023-07-01T12:00:00.000Z');
			const year2024 = await fetchSunMoonPositions('2024-07-01T12:00:00.000Z');
			const year2025 = await fetchSunMoonPositions('2025-07-01T12:00:00.000Z');

			// All should return valid results
			expect(year2023).not.toBeNull();
			expect(year2024).not.toBeNull();
			expect(year2025).not.toBeNull();

			// Similar dates in different years should have similar positions
			// (within a few degrees due to leap years)
			const raDiff = Math.abs(year2023!.sun_ra - year2024!.sun_ra);
			expect(raDiff).toBeLessThan(10); // Allow for some variation
		});

		it('should handle invalid date strings gracefully', async () => {
			// Note: new Date('invalid') creates an Invalid Date, which still has getTime() method
			const result = await fetchSunMoonPositions('invalid-date-string');

			// Should still return a result (even if calculated from Invalid Date)
			expect(result).not.toBeNull();
			expect(typeof result!.sun_ra).toBe('number');
			expect(typeof result!.sun_dec).toBe('number');
			expect(typeof result!.moon_ra).toBe('number');
			expect(typeof result!.moon_dec).toBe('number');
		});

		it('should produce consistent results for same input', async () => {
			const timeOfSignal = '2024-06-15T18:30:00.000Z';

			const result1 = await fetchSunMoonPositions(timeOfSignal);
			const result2 = await fetchSunMoonPositions(timeOfSignal);

			expect(result1).toEqual(result2);
		});

		it('should respect seasonal declination bounds', async () => {
			// Test multiple dates throughout the year
			const dates = [
				'2024-01-01T12:00:00.000Z', // Winter
				'2024-04-01T12:00:00.000Z', // Spring
				'2024-07-01T12:00:00.000Z', // Summer
				'2024-10-01T12:00:00.000Z' // Fall
			];

			for (const date of dates) {
				const result = await fetchSunMoonPositions(date);

				// Sun declination should never exceed ±23.5 degrees (Earth's axial tilt)
				expect(result!.sun_dec).toBeGreaterThanOrEqual(-23.6);
				expect(result!.sun_dec).toBeLessThanOrEqual(23.6);
			}
		});
	});

	// TypeScript interface validation
	describe('Type safety and interface compliance', () => {
		it('should return SunMoonData interface compliant objects', async () => {
			global.fetch = vi.fn().mockRejectedValue(new Error('No network'));

			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			expect(result).not.toBeNull();

			// Type checking through runtime assertions
			const data = result as SunMoonData;
			expect(typeof data.sun_ra).toBe('number');
			expect(typeof data.sun_dec).toBe('number');
			expect(typeof data.moon_ra).toBe('number');
			expect(typeof data.moon_dec).toBe('number');

			// Check that all required properties exist
			expect(data).toHaveProperty('sun_ra');
			expect(data).toHaveProperty('sun_dec');
			expect(data).toHaveProperty('moon_ra');
			expect(data).toHaveProperty('moon_dec');
		});

		it('should handle API response format correctly', async () => {
			const mockApiResponse = {
				sun_ra: 156.789,
				sun_dec: -12.345,
				moon_ra: 246.789,
				moon_dec: 8.123,
				extra_field: 'should be ignored' // API might return extra fields
			};

			global.fetch = vi.fn().mockResolvedValue(createMockFetchResponse(mockApiResponse));

			const result = await fetchSunMoonPositions('2024-01-01T12:00:00.000Z');

			// Should extract only the expected fields
			expect(result).toEqual({
				sun_ra: 156.789,
				sun_dec: -12.345,
				moon_ra: 246.789,
				moon_dec: 8.123
			});
		});
	});
});
