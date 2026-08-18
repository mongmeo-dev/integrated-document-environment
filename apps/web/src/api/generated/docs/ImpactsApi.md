# ImpactsApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**confirmImpactCandidate**](#confirmimpactcandidate) | **PATCH** /api/v1/impacts/candidates/{impact_id}/confirm | Confirm Impact Candidate|
|[**confirmRelationshipCandidate**](#confirmrelationshipcandidate) | **PATCH** /api/v1/impacts/relationships/{relationship_id}/confirm | Confirm Relationship Candidate|
|[**createImpactCandidate**](#createimpactcandidate) | **POST** /api/v1/impacts/candidates | Create Impact Candidate|
|[**createRelationshipCandidate**](#createrelationshipcandidate) | **POST** /api/v1/impacts/relationships | Create Relationship Candidate|
|[**listDocumentImpactCandidates**](#listdocumentimpactcandidates) | **GET** /api/v1/impacts/documents/{document_id} | List Document Candidates|
|[**markImpactModificationNotRequired**](#markimpactmodificationnotrequired) | **PATCH** /api/v1/impacts/candidates/{impact_id}/modification-not-required | Mark Impact Modification Not Required|
|[**markImpactModificationRequired**](#markimpactmodificationrequired) | **PATCH** /api/v1/impacts/candidates/{impact_id}/modification-required | Mark Impact Modification Required|
|[**rejectImpactCandidate**](#rejectimpactcandidate) | **PATCH** /api/v1/impacts/candidates/{impact_id}/reject | Reject Impact Candidate|
|[**rejectRelationshipCandidate**](#rejectrelationshipcandidate) | **PATCH** /api/v1/impacts/relationships/{relationship_id}/reject | Reject Relationship Candidate|

# **confirmImpactCandidate**
> DocumentImpactCandidateResponse confirmImpactCandidate()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let impactId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.confirmImpactCandidate(
    impactId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **impactId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentImpactCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **confirmRelationshipCandidate**
> DocumentRelationshipCandidateResponse confirmRelationshipCandidate()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let relationshipId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.confirmRelationshipCandidate(
    relationshipId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **relationshipId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentRelationshipCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createImpactCandidate**
> DocumentImpactCandidateResponse createImpactCandidate(documentImpactCandidateCreate)


### Example

```typescript
import {
    ImpactsApi,
    Configuration,
    DocumentImpactCandidateCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let documentImpactCandidateCreate: DocumentImpactCandidateCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createImpactCandidate(
    documentImpactCandidateCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentImpactCandidateCreate** | **DocumentImpactCandidateCreate**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentImpactCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**201** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createRelationshipCandidate**
> DocumentRelationshipCandidateResponse createRelationshipCandidate(documentRelationshipCandidateCreate)


### Example

```typescript
import {
    ImpactsApi,
    Configuration,
    DocumentRelationshipCandidateCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let documentRelationshipCandidateCreate: DocumentRelationshipCandidateCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createRelationshipCandidate(
    documentRelationshipCandidateCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentRelationshipCandidateCreate** | **DocumentRelationshipCandidateCreate**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentRelationshipCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**201** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listDocumentImpactCandidates**
> DocumentCandidatesResponse listDocumentImpactCandidates()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listDocumentImpactCandidates(
    documentId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentCandidatesResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **markImpactModificationNotRequired**
> DocumentImpactCandidateResponse markImpactModificationNotRequired()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let impactId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.markImpactModificationNotRequired(
    impactId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **impactId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentImpactCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **markImpactModificationRequired**
> DocumentImpactCandidateResponse markImpactModificationRequired()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let impactId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.markImpactModificationRequired(
    impactId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **impactId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentImpactCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rejectImpactCandidate**
> DocumentImpactCandidateResponse rejectImpactCandidate()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let impactId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.rejectImpactCandidate(
    impactId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **impactId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentImpactCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rejectRelationshipCandidate**
> DocumentRelationshipCandidateResponse rejectRelationshipCandidate()


### Example

```typescript
import {
    ImpactsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ImpactsApi(configuration);

let relationshipId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.rejectRelationshipCandidate(
    relationshipId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **relationshipId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentRelationshipCandidateResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
