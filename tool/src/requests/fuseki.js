import { parseResults, convertResultToMapping } from '../requests/helpers';

const FUSEKI_URL = "http://localhost:3030/result/query"
const PREFIXES = `
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX onto: <http://www.semanticweb.org/nicolas/ontologies/2021/8/patterns#>
`

const getOptions = (query) => {
    return {
        method: 'POST',
        body: `query=${query}`,
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    }
};

export const healthCheck = async () => {
    // test dummy query to check if Fuseki is live
    const query = `
        SELECT ?s ?p ?v
        WHERE {
            ?s ?p ?v
        }
        LIMIT 1
    `
    let response = await fetch( FUSEKI_URL, getOptions(PREFIXES + query) );
    if (response.status === 200) return true;
    return false;
}

export const getSubclasses = async (className) => {
    const query = `
        SELECT ?subject ?label
        WHERE {
            ?subject rdfs:subClassOf ${className}
            OPTIONAL {
                ?subject rdfs:label ?label
            }
        }
    `
    let response = await fetch( FUSEKI_URL, getOptions(PREFIXES + query) );
    if (response.status === 200) {
        return convertResultToMapping(parseResults(await response.json()));
    }
    return [];
}

export const getPatterns = async (filterClasses) => {
    filterClasses = Object.keys(filterClasses);

    const additionalClassTemplate = (additionalClass) => {
        return `{ ?entity rdf:type ${additionalClass} }`
    };

    const queryTemplate = (firstClass, additionalClasses) => {
        return `SELECT ?entity
                    WHERE {
                        { ?entity rdf:type ${firstClass} }.
                        ${additionalClasses}
                    }
                `
    }
    
    let query = "";
    if (filterClasses.length === 0) {
        query = queryTemplate("onto:Pattern", '')
    } else if (filterClasses.length === 1) {
        query = queryTemplate(filterClasses[0], '')
    } else {
        let additionalClasses = "";
        filterClasses.slice(1).forEach(filterClass => {
            additionalClasses += additionalClassTemplate(filterClass);
        })
        query = queryTemplate(filterClasses[0], additionalClasses);
    }

    let response = await fetch( FUSEKI_URL, getOptions(PREFIXES + query) );
    if (response.status === 200) {
        return parseResults(await response.json());
    };
    return [];
}