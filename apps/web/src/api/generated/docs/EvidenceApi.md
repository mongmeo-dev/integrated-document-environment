# EvidenceApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**confirmDocumentEvidenceLinkCandidate**](#confirmdocumentevidencelinkcandidate) | **PATCH** /api/v1/evidence/links/{link_id}/confirm | Confirm Document Evidence Link Candidate|
|[**createDocumentEvidenceLinkCandidate**](#createdocumentevidencelinkcandidate) | **POST** /api/v1/evidence/links | Create Document Evidence Link Candidate|
|[**createEvidenceFile**](#createevidencefile) | **POST** /api/v1/evidence/files | Create Evidence File|
|[**createEvidenceItem**](#createevidenceitem) | **POST** /api/v1/evidence/items | Create Evidence Item|
|[**downloadEvidenceFile**](#downloadevidencefile) | **GET** /api/v1/evidence/{evidence_id}/file | Download Evidence File|
|[**getEvidenceItem**](#getevidenceitem) | **GET** /api/v1/evidence/items/{evidence_id} | Get Evidence Item|
|[**listDocumentEvidenceLinkCandidates**](#listdocumentevidencelinkcandidates) | **GET** /api/v1/evidence/documents/{document_id}/links | List Document Evidence Link Candidates|
|[**listEvidenceItems**](#listevidenceitems) | **GET** /api/v1/evidence/items | List Evidence Items|
|[**markDocumentEvidenceLinksStale**](#markdocumentevidencelinksstale) | **PATCH** /api/v1/evidence/documents/{document_id}/links/stale | Mark Document Evidence Links Stale|
|[**markEvidenceLinksStale**](#markevidencelinksstale) | **PATCH** /api/v1/evidence/items/{evidence_id}/links/stale | Mark Evidence Links Stale|
|[**rejectDocumentEvidenceLinkCandidate**](#rejectdocumentevidencelinkcandidate) | **PATCH** /api/v1/evidence/links/{link_id}/reject | Reject Document Evidence Link Candidate|
|[**reviewDocumentEvidenceLinkFreshness**](#reviewdocumentevidencelinkfreshness) | **PATCH** /api/v1/evidence/links/{link_id}/freshness-review | Review Document Evidence Link Freshness|
|[**updateEvidenceItem**](#updateevidenceitem) | **PATCH** /api/v1/evidence/items/{evidence_id} | Update Evidence Item|

# **confirmDocumentEvidenceLinkCandidate**
> DocumentEvidenceLinkResponse confirmDocumentEvidenceLinkCandidate()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let linkId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.confirmDocumentEvidenceLinkCandidate(
    linkId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **linkId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentEvidenceLinkResponse**

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

# **createDocumentEvidenceLinkCandidate**
> DocumentEvidenceLinkResponse createDocumentEvidenceLinkCandidate(documentEvidenceLinkCreate)


### Example

```typescript
import {
    EvidenceApi,
    Configuration,
    DocumentEvidenceLinkCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let documentEvidenceLinkCreate: DocumentEvidenceLinkCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createDocumentEvidenceLinkCandidate(
    documentEvidenceLinkCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **documentEvidenceLinkCreate** | **DocumentEvidenceLinkCreate**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentEvidenceLinkResponse**

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

# **createEvidenceFile**
> EvidenceItemResponse createEvidenceFile()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let title: string; // (default to undefined)
let description: string; // (default to undefined)
let file: File; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)
let version: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createEvidenceFile(
    title,
    description,
    file,
    ideSession,
    version
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **title** | [**string**] |  | defaults to undefined|
| **description** | [**string**] |  | defaults to undefined|
| **file** | [**File**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|
| **version** | [**string**] |  | (optional) defaults to undefined|


### Return type

**EvidenceItemResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**201** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**422** | Unprocessable Content |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createEvidenceItem**
> EvidenceItemResponse createEvidenceItem(evidenceItemCreate)


### Example

```typescript
import {
    EvidenceApi,
    Configuration,
    EvidenceItemCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let evidenceItemCreate: EvidenceItemCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createEvidenceItem(
    evidenceItemCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **evidenceItemCreate** | **EvidenceItemCreate**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**EvidenceItemResponse**

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

# **downloadEvidenceFile**
> any downloadEvidenceFile()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let evidenceId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.downloadEvidenceFile(
    evidenceId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **evidenceId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**any**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getEvidenceItem**
> EvidenceItemResponse getEvidenceItem()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let evidenceId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getEvidenceItem(
    evidenceId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **evidenceId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**EvidenceItemResponse**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listDocumentEvidenceLinkCandidates**
> Array<DocumentEvidenceLinkResponse> listDocumentEvidenceLinkCandidates()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listDocumentEvidenceLinkCandidates(
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

**Array<DocumentEvidenceLinkResponse>**

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
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listEvidenceItems**
> Array<EvidenceItemResponse> listEvidenceItems()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listEvidenceItems(
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**Array<EvidenceItemResponse>**

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

# **markDocumentEvidenceLinksStale**
> markDocumentEvidenceLinksStale()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.markDocumentEvidenceLinksStale(
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

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**204** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **markEvidenceLinksStale**
> markEvidenceLinksStale()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let evidenceId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.markEvidenceLinksStale(
    evidenceId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **evidenceId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**204** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rejectDocumentEvidenceLinkCandidate**
> DocumentEvidenceLinkResponse rejectDocumentEvidenceLinkCandidate()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let linkId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.rejectDocumentEvidenceLinkCandidate(
    linkId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **linkId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentEvidenceLinkResponse**

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

# **reviewDocumentEvidenceLinkFreshness**
> DocumentEvidenceLinkResponse reviewDocumentEvidenceLinkFreshness()


### Example

```typescript
import {
    EvidenceApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let linkId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.reviewDocumentEvidenceLinkFreshness(
    linkId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **linkId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**DocumentEvidenceLinkResponse**

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

# **updateEvidenceItem**
> EvidenceItemResponse updateEvidenceItem(evidenceItemUpdate)


### Example

```typescript
import {
    EvidenceApi,
    Configuration,
    EvidenceItemUpdate
} from './api';

const configuration = new Configuration();
const apiInstance = new EvidenceApi(configuration);

let evidenceId: string; // (default to undefined)
let evidenceItemUpdate: EvidenceItemUpdate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.updateEvidenceItem(
    evidenceId,
    evidenceItemUpdate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **evidenceItemUpdate** | **EvidenceItemUpdate**|  | |
| **evidenceId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**EvidenceItemResponse**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Successful Response |  -  |
|**401** | Unauthorized |  -  |
|**404** | Not Found |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
