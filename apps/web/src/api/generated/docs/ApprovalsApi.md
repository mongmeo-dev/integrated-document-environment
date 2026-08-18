# ApprovalsApi

All URIs are relative to *http://localhost*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**approveApprovalStep**](#approveapprovalstep) | **POST** /api/v1/approvals/steps/{step_id}/approve | Approve Approval Step|
|[**createApprovalWorkflow**](#createapprovalworkflow) | **POST** /api/v1/approvals | Create Approval Workflow|
|[**getApprovalWorkflow**](#getapprovalworkflow) | **GET** /api/v1/approvals/{workflow_id} | Get Approval Workflow|
|[**getDocumentApprovalWorkflow**](#getdocumentapprovalworkflow) | **GET** /api/v1/approvals/documents/{document_id} | Get Document Approval Workflow|
|[**listApprovalWorkflowAudits**](#listapprovalworkflowaudits) | **GET** /api/v1/approvals/{workflow_id}/audits | List Approval Workflow Audits|
|[**startApprovalWorkflow**](#startapprovalworkflow) | **POST** /api/v1/approvals/{workflow_id}/start | Start Approval Workflow|
|[**updateApprovalStep**](#updateapprovalstep) | **PATCH** /api/v1/approvals/steps/{step_id} | Update Approval Step|

# **approveApprovalStep**
> ApprovalWorkflowResponse approveApprovalStep()


### Example

```typescript
import {
    ApprovalsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let stepId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.approveApprovalStep(
    stepId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **stepId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ApprovalWorkflowResponse**

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
|**403** | Forbidden |  -  |
|**404** | Not Found |  -  |
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createApprovalWorkflow**
> ApprovalWorkflowResponse createApprovalWorkflow(approvalWorkflowCreate)


### Example

```typescript
import {
    ApprovalsApi,
    Configuration,
    ApprovalWorkflowCreate
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let approvalWorkflowCreate: ApprovalWorkflowCreate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.createApprovalWorkflow(
    approvalWorkflowCreate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **approvalWorkflowCreate** | **ApprovalWorkflowCreate**|  | |
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ApprovalWorkflowResponse**

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
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getApprovalWorkflow**
> ApprovalWorkflowResponse getApprovalWorkflow()


### Example

```typescript
import {
    ApprovalsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let workflowId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getApprovalWorkflow(
    workflowId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **workflowId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ApprovalWorkflowResponse**

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

# **getDocumentApprovalWorkflow**
> ApprovalWorkflowResponse getDocumentApprovalWorkflow()


### Example

```typescript
import {
    ApprovalsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let documentId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.getDocumentApprovalWorkflow(
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

**ApprovalWorkflowResponse**

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

# **listApprovalWorkflowAudits**
> Array<ApprovalWorkflowAuditResponse> listApprovalWorkflowAudits()


### Example

```typescript
import {
    ApprovalsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let workflowId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.listApprovalWorkflowAudits(
    workflowId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **workflowId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**Array<ApprovalWorkflowAuditResponse>**

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

# **startApprovalWorkflow**
> ApprovalWorkflowResponse startApprovalWorkflow()


### Example

```typescript
import {
    ApprovalsApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let workflowId: string; // (default to undefined)
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.startApprovalWorkflow(
    workflowId,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **workflowId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ApprovalWorkflowResponse**

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

# **updateApprovalStep**
> ApprovalStepResponse updateApprovalStep(approvalStepUpdate)


### Example

```typescript
import {
    ApprovalsApi,
    Configuration,
    ApprovalStepUpdate
} from './api';

const configuration = new Configuration();
const apiInstance = new ApprovalsApi(configuration);

let stepId: string; // (default to undefined)
let approvalStepUpdate: ApprovalStepUpdate; //
let ideSession: string; // (optional) (default to undefined)

const { status, data } = await apiInstance.updateApprovalStep(
    stepId,
    approvalStepUpdate,
    ideSession
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **approvalStepUpdate** | **ApprovalStepUpdate**|  | |
| **stepId** | [**string**] |  | defaults to undefined|
| **ideSession** | [**string**] |  | (optional) defaults to undefined|


### Return type

**ApprovalStepResponse**

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
|**409** | Conflict |  -  |
|**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
