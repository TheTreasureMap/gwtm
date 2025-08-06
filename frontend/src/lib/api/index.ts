import { pointingService } from './services/pointing.service';
import { alertService } from './services/alert.service';
import { candidateService } from './services/candidate.service';
import { instrumentService } from './services/instrument.service';
import { galaxyService } from './services/galaxy.service';
import { doiService } from './services/doi.service';
import { icecubeService } from './services/icecube.service';
import { miscService } from './services/misc.service';
import { ajaxService } from './services/ajax.service';
import { authService } from './services/auth.service';
import { searchService } from './services/search.service';

export const api = {
    pointings: pointingService,
    alerts: alertService,
    candidates: candidateService,
    instruments: instrumentService,
    galaxies: galaxyService,
    doi: doiService,
    icecube: icecubeService,
    misc: miscService,
    ajax: ajaxService,
    auth: authService,
    search: searchService
};

export * from './types/alert.types';
export * from './types/candidate.types';
export * from './types/doi.types';
export * from './types/galaxy.types';
export * from './types/instrument.types';
export * from './types/icecube.types';
export * from './types/misc.types';
export * from './types/pointing.types';