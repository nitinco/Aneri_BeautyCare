/* Admin UI helpers: offers, products, bills, deliveries, complaints */

document.addEventListener('DOMContentLoaded', async function() {
    if (!window.apiClient) return;

    if (document.getElementById('offersTableBody')) await loadOffersPage();
    if (document.getElementById('productsTableBody')) await loadProductsPage();
    if (document.getElementById('billsTableBody')) await loadBillsPage();
    if (document.getElementById('packageBookingsTableBody')) await loadPackageBookingsPage();
    if (document.getElementById('complaintsTableBody')) await loadComplaintsPage();
    if (document.getElementById('deliveryOrdersBody')) await loadDeliveryPage();
    if (document.getElementById('ordersTableBody')) await loadOrdersPage();
    if (document.getElementById('customersTableBody')) await loadCustomersPage();
    if (document.getElementById('usersTableBody')) await loadUsersPage();
    if (document.getElementById('staffTableBody')) await loadStaffPage();
    if (document.getElementById('brandsTableBody')) await loadBrandsPage();
    if (document.getElementById('appointmentsTableBody')) await loadAppointmentsPage();
    if (document.getElementById('stockTableBody')) await loadStockPage();
    if (document.getElementById('suppliersTableBody')) await loadSuppliersPage();
    if (document.getElementById('stockTableBody')) await populateStockSelects();
});

async function loadOffersPage() {
    try {
        LoadingOverlay.show('Loading offers...');
        const res = await apiClient.getOffers();
        const offers = res.offers || [];
        const tbody = document.getElementById('offersTableBody');
        tbody.innerHTML = '';
        offers.forEach(o => {
            let offerType = 'General';
            let appliesTo = 'All items';
            
            if (o.product_name) {
                offerType = 'Product';
                appliesTo = o.product_name;
            } else if (o.service_name) {
                offerType = 'Service';
                appliesTo = o.service_name;
            }
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${o.id}</td>
                <td>${o.title}</td>
                <td>${offerType}</td>
                <td>${appliesTo}</td>
                <td>${o.discount_percent || 0}%</td>
                <td>${o.is_active ? 'Active' : 'Inactive'}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" data-id="${o.id}" onclick="editOffer(${o.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteOffer(${o.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
        Toast.error('Failed to load offers');
    } finally {
        LoadingOverlay.hide();
    }
}

async function editOffer(id) {
    try {
        const title = prompt('Offer title:');
        if (title === null) return;
        const description = prompt('Description:');
        const is_active = confirm('Activate offer?');
        await apiClient.updateOffer(id, { title, description, is_active });
        Toast.success('Offer updated');
        loadOffersPage();
    } catch (err) {
        console.error(err);
        Toast.error('Failed to update offer');
    }
}

async function deleteOffer(id) {
    if (!confirm('Delete offer #' + id + '?')) return;
    try {
        LoadingOverlay.show('Deleting offer...');
        await apiClient.deleteOffer(id);
        Toast.success('Offer deleted');
        loadOffersPage();
    } catch (err) {
        console.error('deleteOffer error', err);
        Toast.error(err.message || 'Failed to delete offer');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadProductsPage() {
    try {
        LoadingOverlay.show('Loading products...');
        const res = await apiClient.getProducts();
        const products = res.products || [];
        const tbody = document.getElementById('productsTableBody');
        tbody.innerHTML = '';
        products.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.id}</td>
                <td>${p.name}</td>
                <td>${p.brand_name || p.brand_id || ''}</td>
                <td>${p.sku || ''}</td>
                <td>${p.price}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" onclick="openEditProduct(${p.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProduct(${p.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
        Toast.error('Failed to load products');
    } finally {
        LoadingOverlay.hide();
    }
}

// product modal state
window._editingProductId = null;

function openEditProduct(id) {
    // Fetch full product details for editing
    fetch(`/api/products/${id}`)
        .then(res => res.json())
        .then(product => {
            window._editingProductId = id;
            document.getElementById('productName').value = product.name || '';
            document.getElementById('productBrand').value = product.brand_id || '';
            document.getElementById('productSKU').value = product.sku || '';
            document.getElementById('productPrice').value = parseFloat(product.price) || 0;
            document.getElementById('productImage').value = '';
            
            // Show current image if exists
            const currentImageContainer = document.getElementById('currentProductImageContainer');
            const currentImage = document.getElementById('currentProductImage');
            if (product.image) {
                currentImage.src = `/static/${product.image}`;
                currentImageContainer.style.display = 'block';
            } else {
                currentImageContainer.style.display = 'none';
            }
            
            var modal = new bootstrap.Modal(document.getElementById('productModal'));
            modal.show();
        })
        .catch(err => {
            console.error('Failed to fetch product details', err);
            Toast.error('Failed to load product details');
        });
}

async function saveProductFromModal() {
    if (window._savingProduct) return; // prevent duplicate submissions
    window._savingProduct = true;
    document.getElementById('saveProductBtn')?.setAttribute('disabled', 'disabled');

    const formData = new FormData();
    formData.append('name', document.getElementById('productName').value.trim());
    formData.append('brand_id', document.getElementById('productBrand').value || null);
    formData.append('sku', document.getElementById('productSKU').value.trim());
    formData.append('price', parseFloat(document.getElementById('productPrice').value) || 0);
    
    const imageFile = document.getElementById('productImage').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    if (!formData.get('name')) { 
        Toast.error('Name required'); 
        window._savingProduct = false;
        document.getElementById('saveProductBtn')?.removeAttribute('disabled');
        return; 
    }

    try {
        LoadingOverlay.show('Saving product...');
        if (window._editingProductId) {
            await apiClient.updateProduct(window._editingProductId, formData);
            Toast.success('Product updated');
            window._editingProductId = null;
        } else {
            await apiClient.createProduct(formData);
            Toast.success('Product created');
        }
        var modal = bootstrap.Modal.getInstance(document.getElementById('productModal')) || new bootstrap.Modal(document.getElementById('productModal'));
        modal.hide();
        loadProductsPage();
    } catch (e) {
        console.error(e);
        Toast.error('Failed to save product');
    } finally {
        LoadingOverlay.hide();
        window._savingProduct = false;
        document.getElementById('saveProductBtn')?.removeAttribute('disabled');
    }
}

async function deleteProduct(id) {
    if (!confirm('Delete product #' + id + '?')) return;
    try {
        LoadingOverlay.show('Deleting product...');
        await apiClient.deleteProduct(id);
        Toast.success('Product deleted');
        loadProductsPage();
    } catch (e) {
        console.error(e);
        Toast.error('Failed to delete product');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadBillsPage() {
    try {
        LoadingOverlay.show('Loading bills...');
        const tbody = document.getElementById('billsTableBody');
        tbody.innerHTML = '';

        // Load regular bills
        try {
            const bills = await apiClient.listBills();
            bills.forEach(b => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${b.id}</td>
                    <td><span class="badge bg-primary">Bill</span></td>
                    <td>${b.customer_id}</td>
                    <td>${b.created_at}</td>
                    <td>₹${parseFloat(b.total_amount).toFixed(2)}</td>
                    <td><span class="badge bg-success">Paid</span></td>
                    <td><a class="btn btn-sm btn-outline-primary" href="${apiClient.getBillPDF(b.id)}" target="_blank">Download PDF</a></td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.warn('Failed to load regular bills:', e);
        }

        // Load package booking bills
        try {
            const packageBookings = await apiClient.get('/api/package/admin/bookings');
            const bookings = Array.isArray(packageBookings) ? packageBookings : (packageBookings.bookings || []);

            bookings.forEach(b => {
                const paymentStatus = b.razorpay_payment_id ? 'Paid' : 'Pending';
                const statusBadge = paymentStatus === 'Paid' ? 'bg-success' : 'bg-warning text-dark';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${b.id}</td>
                    <td><span class="badge bg-info">Package Booking</span></td>
                    <td>${b.customer_name || b.customer_id || 'N/A'}</td>
                    <td>${b.created_at ? new Date(b.created_at).toLocaleDateString() : 'N/A'}</td>
                    <td>₹${parseFloat(b.total_amount || 0).toFixed(2)}</td>
                    <td><span class="badge ${statusBadge}">${paymentStatus}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-info me-1" onclick="viewPackageBookingDetails(${b.id})">
                            <i class="bi bi-eye"></i> View
                        </button>
                        ${!b.razorpay_payment_id ? '<span class="text-muted small">No PDF</span>' : '<span class="text-success small">✓ Paid</span>'}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.warn('Failed to load package booking bills:', e);
        }

        // Show message if no bills found
        if (tbody.children.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="bi bi-receipt" style="font-size: 2rem;"></i>
                        <p class="mt-2 mb-0">No bills found</p>
                    </td>
                </tr>
            `;
        }

    } catch (err) {
        console.error(err);
        Toast.error('Failed to load bills');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadComplaintsPage() {
    try {
        LoadingOverlay.show('Loading complaints...');
        const complaints = await apiClient.listComplaints();
        const tbody = document.getElementById('complaintsTableBody');
        tbody.innerHTML = '';
        complaints.forEach(c => {
            const tr = document.createElement('tr');
            const customerName = c.customer_name || c.customer_id || '';
            tr.innerHTML = `
                <td>${c.id}</td>
                <td>${customerName}</td>
                <td>${c.subject}</td>
                <td>${c.message}</td>
                <td>${c.status || 'open'}</td>
                <td><button class="btn btn-sm btn-success" onclick="reviewComplaint(${c.id})">Mark Reviewed</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
        Toast.error('Failed to load complaints');
    } finally {
        LoadingOverlay.hide();
    }
}

async function reviewComplaint(id) {
    try {
        const reviewed_by = prompt('Reviewer name:');
        await apiClient.reviewComplaint(id, { status: 'reviewed', reviewed_by });
        Toast.success('Complaint reviewed');
        loadComplaintsPage();
    } catch (err) {
        console.error(err);
        Toast.error('Failed to review complaint');
    }
}

async function loadDeliveryPage() {
    try {
        LoadingOverlay.show('Loading deliveries...');
        // For simplicity, list orders to create deliveries
        const resp = await apiClient.get('/orders');
        const orders = Array.isArray(resp) ? resp : resp.orders || [];
        const tbody = document.getElementById('deliveryOrdersBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        orders.forEach(o => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${o.id}</td>
                <td>${o.customer_name || o.customer_id || o.customer || ''}</td>
                <td>₹${parseFloat(o.total || o.total_amount || 0).toFixed(2)}</td>
                <td><button class="btn btn-sm btn-primary" onclick="createDelivery(${o.id})">Create Delivery</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
        Toast.error('Failed to load orders');
    } finally {
        LoadingOverlay.hide();
    }
}

async function createDelivery(orderId) {
    try {
        await apiClient.createDelivery({ order_id: orderId });
        Toast.success('Delivery created');
        // refresh both deliveries and orders to reflect status changes
        await loadDeliveryPage();
        await loadOrdersPage();
    } catch (err) {
        console.error(err);
        Toast.error('Failed to create delivery');
    }
}

async function loadOrdersPage() {
    try {
        LoadingOverlay.show('Loading orders...');
        const resp = await apiClient.get('/orders');
        const orders = Array.isArray(resp) ? resp : resp.orders || [];
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        orders.forEach(o => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${o.id}</td>
                <td>${o.customer_name || o.customer_id || ''}</td>
                <td>${o.status || ''}</td>
                <td>₹${parseFloat(o.total || o.total_amount || 0).toFixed(2)}</td>
                <td>${o.created_at || o.created || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadOrdersPage error', err);
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadAppointmentsPage() {
    try {
        LoadingOverlay.show('Loading appointments...');
        // use apiClient helper added to static/js/api.js
        const resp = await apiClient.listAppointments();
        // resp may be an object with appointments or an array
        const appts = Array.isArray(resp) ? resp : (resp.appointments || resp);
        const tbody = document.getElementById('appointmentsTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        appts.forEach(a => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${a.id}</td>
                <td>${a.customer_name || a.customer_id || ''}</td>
                <td>${a.service_name || a.service_id || ''}</td>
                <td>${a.staff_name || (a.staff_id || '')}</td>
                <td>${a.start_datetime || ''}</td>
                <td>${a.end_datetime || ''}</td>
                <td>${a.status || ''}</td>
                <td>${a.created_display || a.created_at || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadAppointmentsPage error', err);
        Toast.error('Failed to load appointments');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadStockPage() {
    try {
        LoadingOverlay.show('Loading inventory...');
        const resp = await apiClient.getStock();
        // resp may be array or object
        const stocks = Array.isArray(resp) ? resp : (resp || []);
        const tbody = document.getElementById('stockTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        stocks.forEach(s => {
            const tr = document.createElement('tr');
            // store ids for edit operations
            if (s.product_id) tr.dataset.productId = s.product_id;
            if (s.supplier_id) tr.dataset.supplierId = s.supplier_id;
            const qty = Number(s.quantity || 0);
            const reorder = Number(s.reorder_level || 0);
            tr.innerHTML = `
                <td>${s.id}</td>
                <td>${s.product_name || s.product_id || ''}</td>
                <td>${s.supplier_name || s.supplier_id || ''}</td>
                <td class="stock-qty">${qty}</td>
                <td>${reorder}</td>
                <td>${s.updated_at || s.created_at || ''}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" onclick="openEditStock(${s.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteStock(${s.id})">Delete</button>
                </td>
            `;
            if (qty <= reorder) tr.classList.add('table-danger');
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadStockPage error', err);
        Toast.error('Failed to load inventory');
    } finally {
        LoadingOverlay.hide();
    }
}

async function populateStockSelects() {
    try {
        const prodResp = await apiClient.getProducts();
        const supResp = await apiClient.getSuppliers();
        const products = prodResp.products || [];
        const suppliers = supResp.suppliers || [];
        const prodSel = document.getElementById('stockProductSelect');
        const supSel = document.getElementById('stockSupplierSelect');
        if (prodSel) {
            // clear and add default
            prodSel.innerHTML = '<option value="">-- select product --</option>';
            products.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name || p.id;
                prodSel.appendChild(opt);
            });
        }
        if (supSel) {
            supSel.innerHTML = '<option value="">-- select supplier --</option>';
            suppliers.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.name || s.id;
                supSel.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('populateStockSelects error', err);
    }
}

function openEditStock(id) {
    // find row data from table or fetch single stock via API if needed
    const rows = document.querySelectorAll('#stockTableBody tr');
    let found = null;
    rows.forEach(r => {
        const cols = r.querySelectorAll('td');
        if (cols && Number(cols[0].textContent) === Number(id)) {
            found = {
                id: id,
                product_id: cols[1].textContent || '',
                supplier_id: cols[2].textContent || '',
                quantity: cols[3].textContent || 0,
                reorder_level: cols[4].textContent || 0
            };
        }
    });
    if (found) {
        document.getElementById('stockModalTitle').textContent = 'Edit Stock';
        document.getElementById('stockId').value = found.id;
        // set selects by data attributes stored on row (product/supplier ids)
        const row = document.querySelector(`#stockTableBody tr td:first-child:contains('${id}')`);
        // fallback: use dataset from previously captured `found` object by scanning rows
        const rows = document.querySelectorAll('#stockTableBody tr');
        let targetRow = null;
        rows.forEach(r => { if (Number(r.querySelector('td').textContent) === Number(id)) targetRow = r; });
        if (targetRow) {
            const pid = targetRow.dataset.productId || '';
            const sid = targetRow.dataset.supplierId || '';
            document.getElementById('stockProductSelect').value = pid || '';
            document.getElementById('stockSupplierSelect').value = sid || '';
        } else {
            document.getElementById('stockProductSelect').value = '';
            document.getElementById('stockSupplierSelect').value = '';
        }
        document.getElementById('stockQuantity').value = found.quantity || 0;
        document.getElementById('stockReorderLevel').value = found.reorder_level || 5;
        var modal = new bootstrap.Modal(document.getElementById('stockModal'));
        modal.show();
    }
}

function openAddStock() {
    window._editingStockId = null;
    document.getElementById('stockModalTitle').textContent = 'Add Stock';
    document.getElementById('stockId').value = '';
    document.getElementById('stockProductSelect').value = '';
    document.getElementById('stockSupplierSelect').value = '';
    document.getElementById('stockQuantity').value = 0;
    document.getElementById('stockReorderLevel').value = 5;
    var modal = new bootstrap.Modal(document.getElementById('stockModal'));
    modal.show();
}

async function saveStockFromModal() {
    if (window._savingStock) return;
    window._savingStock = true;
    document.getElementById('saveStockBtn')?.setAttribute('disabled', 'disabled');
    try {
        const id = document.getElementById('stockId').value;
        const payload = {
            product_id: document.getElementById('stockProductSelect').value ? Number(document.getElementById('stockProductSelect').value) : null,
            supplier_id: document.getElementById('stockSupplierSelect').value ? Number(document.getElementById('stockSupplierSelect').value) : null,
            quantity: Number(document.getElementById('stockQuantity').value) || 0,
            reorder_level: Number(document.getElementById('stockReorderLevel').value) || 0
        };
        LoadingOverlay.show('Saving stock...');
        if (id) {
            await apiClient.updateStock(id, payload);
            Toast.success('Stock updated');
        } else {
            await apiClient.createStock(payload);
            Toast.success('Stock created');
        }
        var modal = bootstrap.Modal.getInstance(document.getElementById('stockModal')) || new bootstrap.Modal(document.getElementById('stockModal'));
        modal.hide();
        loadStockPage();
    } catch (err) {
        console.error('saveStockFromModal error', err);
        Toast.error(err.message || 'Failed to save stock');
    } finally {
        LoadingOverlay.hide();
        window._savingStock = false;
        document.getElementById('saveStockBtn')?.removeAttribute('disabled');
    }
}

async function deleteStock(id) {
    if (!confirm('Delete stock #' + id + '?')) return;
    try {
        LoadingOverlay.show('Deleting stock...');
        await apiClient.deleteStock(id);
        Toast.success('Stock deleted');
        loadStockPage();
    } catch (err) {
        console.error('deleteStock error', err);
        Toast.error(err.message || 'Failed to delete stock');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadCustomersPage() {
    try {
        LoadingOverlay.show('Loading customers...');
        const resp = await apiClient.getCustomers();
        const customers = Array.isArray(resp) ? resp : resp.customers || [];
        const tbody = document.getElementById('customersTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        customers.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.id}</td>
                <td>${c.name || c.full_name || c.username || ''}</td>
                <td>${c.email || ''}</td>
                <td>${c.phone || c.mobile || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadCustomersPage error', err);
        Toast.error('Failed to load customers');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadUsersPage() {
    try {
        LoadingOverlay.show('Loading users...');
        const resp = await apiClient.getUsers();
        const users = Array.isArray(resp) ? resp : resp.users || [];
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.name || ''}</td>
                <td>${u.email || ''}</td>
                <td>${u.role || ''}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadUsersPage error', err);
        Toast.error('Failed to load users');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadStaffPage() {
    try {
        LoadingOverlay.show('Loading staff...');
        const resp = await apiClient.getStaffs();
        const staffs = Array.isArray(resp) ? resp : resp.staff || [];
        const tbody = document.getElementById('staffTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        staffs.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.id}</td>
                <td>${s.name || ''}</td>
                <td>${s.email || s.user_id || ''}</td>
                <td>${s.phone || ''}</td>
                <td>${s.is_active ? 'Yes' : 'No'}</td>
                <td>${s.is_available ? 'Yes' : 'No'}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" onclick="openEditStaff(${s.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteStaff(${s.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadStaffPage error', err);
        Toast.error('Failed to load staff');
    } finally {
        LoadingOverlay.hide();
    }
}

// Staff edit/delete state
window._editingStaffId = null;

function openAddStaffModal() {
    window._editingStaffId = null;
    document.getElementById('staffModalTitle').textContent = 'Add Staff';
    document.getElementById('staffName').value = '';
    document.getElementById('staffEmail').value = '';
    document.getElementById('staffPassword').value = '';
    document.getElementById('staffPhone').value = '';
    var modal = new bootstrap.Modal(document.getElementById('staffModal'));
    modal.show();
}

function openEditStaff(id) {
    const rows = document.querySelectorAll('#staffTableBody tr');
    let found = null;
    rows.forEach(r => {
        const cols = r.querySelectorAll('td');
        if (cols && Number(cols[0].textContent) === Number(id)) {
            found = { id: id, name: cols[1].textContent, phone: cols[3].textContent, email: cols[2].textContent || '' };
        }
    });
    if (found) {
        window._editingStaffId = id;
        document.getElementById('staffModalTitle').textContent = 'Edit Staff';
        document.getElementById('staffName').value = found.name || '';
        document.getElementById('staffEmail').value = found.email || '';
        document.getElementById('staffPassword').value = '';
        document.getElementById('staffPhone').value = found.phone || '';
        var modal = new bootstrap.Modal(document.getElementById('staffModal'));
        modal.show();
    }
}

async function saveStaffFromModal() {
    const name = document.getElementById('staffName').value.trim();
    const email = document.getElementById('staffEmail').value.trim();
    const password = document.getElementById('staffPassword').value;
    const phone = document.getElementById('staffPhone').value.trim();
    if (!name || !email) { Toast.error('Name and email required'); return; }
    try {
        LoadingOverlay.show('Saving staff...');
        if (window._editingStaffId) {
            const payload = { name, email, phone };
            if (password) payload.password = password; // only send if changed
            await apiClient.updateStaff(window._editingStaffId, payload);
            Toast.success('Staff updated');
            window._editingStaffId = null;
        } else {
            if (!password) { Toast.error('Password required for new staff'); return; }
            await apiClient.createStaff({ name, email, password, phone });
            Toast.success('Staff created');
        }
        var modal = bootstrap.Modal.getInstance(document.getElementById('staffModal')) || new bootstrap.Modal(document.getElementById('staffModal'));
        modal.hide();
        loadStaffPage();
    } catch (err) {
        console.error('saveStaffFromModal error', err);
        Toast.error(err.message || 'Failed to save staff');
    } finally {
        LoadingOverlay.hide();
    }
}

async function deleteStaff(id) {
    if (!confirm('Delete staff #' + id + '?')) return;
    try {
        LoadingOverlay.show('Deleting staff...');
        await apiClient.deleteStaff(id);
        Toast.success('Staff deleted');
        loadStaffPage();
    } catch (err) {
        console.error('deleteStaff error', err);
        Toast.error(err.message || 'Failed to delete staff');
    } finally {
        LoadingOverlay.hide();
    }
}

async function loadBrandsPage() {
    try {
        LoadingOverlay.show('Loading brands...');
        const resp = await apiClient.getBrands();
        const brands = Array.isArray(resp) ? resp : resp.brands || [];
        const tbody = document.getElementById('brandsTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        brands.forEach(b => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${b.id}</td>
                <td>${b.name || ''}</td>
                <td>${b.description || ''}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" onclick="openEditBrand(${b.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteBrand(${b.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadBrandsPage error', err);
        Toast.error('Failed to load brands');
    } finally {
        LoadingOverlay.hide();
    }
}

async function saveBrandFromModal() {
    const name = document.getElementById('brandName').value.trim();
    const description = document.getElementById('brandDescription').value.trim();
    if (!name) { Toast.error('Name required'); return; }
    try {
        LoadingOverlay.show('Saving brand...');
        if (window._editingBrandId) {
            await apiClient.updateBrand(window._editingBrandId, { name, description });
            Toast.success('Brand updated');
            window._editingBrandId = null;
        } else {
            await apiClient.createBrand({ name, description });
            Toast.success('Brand created');
        }
        var modal = bootstrap.Modal.getInstance(document.getElementById('brandModal')) || new bootstrap.Modal(document.getElementById('brandModal'));
        modal.hide();
        loadBrandsPage();
        // refresh product brand select if present
        try { populateProductBrandSelect(); } catch (e) { /* ignore */ }
    } catch (err) {
        console.error('saveBrandFromModal error', err);
        Toast.error('Failed to create brand');
    } finally {
        LoadingOverlay.hide();
    }
}

// brand modal edit state
window._editingBrandId = null;

function openEditBrand(id) {
    const rows = document.querySelectorAll('#brandsTableBody tr');
    let found = null;
    rows.forEach(r => {
        const cols = r.querySelectorAll('td');
        if (cols && Number(cols[0].textContent) === Number(id)) {
            found = { id: id, name: cols[1].textContent, description: cols[2].textContent };
        }
    });
    if (found) {
        window._editingBrandId = id;
        document.getElementById('brandName').value = found.name || '';
        document.getElementById('brandDescription').value = found.description || '';
        var modal = new bootstrap.Modal(document.getElementById('brandModal'));
        modal.show();
    }
}

async function deleteBrand(id) {
    if (!confirm('Delete brand #' + id + '?')) return;
    try {
        LoadingOverlay.show('Deleting brand...');
        await apiClient.deleteBrand(id);
        Toast.success('Brand deleted');
        loadBrandsPage();
        try { populateProductBrandSelect(); } catch (e) {}
    } catch (err) {
        console.error('deleteBrand error', err);
        Toast.error(err.message || 'Failed to delete brand');
    } finally {
        LoadingOverlay.hide();
    }
}

// populate productBrand select if present on page
async function populateProductBrandSelect() {
    const sel = document.getElementById('productBrand');
    if (!sel) return;
    try {
        const b = await apiClient.getBrands();
        const brands = Array.isArray(b) ? b : (b.brands || []);
        sel.innerHTML = '<option value="">-- none --</option>';
        brands.forEach(x => { const opt = document.createElement('option'); opt.value = x.id; opt.textContent = x.name; sel.appendChild(opt); });
    } catch (e) {
        console.warn('populateProductBrandSelect failed', e);
    }
}

// Suppliers: load, add, edit, delete
window._editingSupplierId = null;

async function loadSuppliersPage() {
    try {
        LoadingOverlay.show('Loading suppliers...');
        const resp = await apiClient.getSuppliers();
        const suppliers = Array.isArray(resp) ? resp : (resp.suppliers || []);
        const tbody = document.getElementById('suppliersTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        suppliers.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.id}</td>
                <td>${s.name || ''}</td>
                <td>${s.contact || ''}</td>
                <td>${s.address || ''}</td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" onclick="openEditSupplier(${s.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSupplier(${s.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadSuppliersPage error', err);
        Toast.error('Failed to load suppliers');
    } finally {
        LoadingOverlay.hide();
    }
}

function openEditSupplier(id) {
    const rows = document.querySelectorAll('#suppliersTableBody tr');
    let found = null;
    rows.forEach(r => {
        const cols = r.querySelectorAll('td');
        if (cols && Number(cols[0].textContent) === Number(id)) {
            found = { id: id, name: cols[1].textContent, contact: cols[2].textContent, address: cols[3].textContent };
        }
    });
    if (found) {
        window._editingSupplierId = id;
        document.getElementById('supplierName').value = found.name || '';
        document.getElementById('supplierContact').value = found.contact || '';
        document.getElementById('supplierAddress').value = found.address || '';
        var modal = new bootstrap.Modal(document.getElementById('supplierModal'));
        modal.show();
    }
}

async function saveSupplierFromModal() {
    const name = document.getElementById('supplierName').value.trim();
    const contact = document.getElementById('supplierContact').value.trim();
    const address = document.getElementById('supplierAddress').value.trim();
    if (!name) { Toast.error('Name required'); return; }
    try {
        LoadingOverlay.show('Saving supplier...');
        if (window._editingSupplierId) {
            await apiClient.updateSupplier(window._editingSupplierId, { name, contact, address });
            Toast.success('Supplier updated');
            window._editingSupplierId = null;
        } else {
            await apiClient.createSupplier({ name, contact, address });
            Toast.success('Supplier created');
        }
        var modal = bootstrap.Modal.getInstance(document.getElementById('supplierModal')) || new bootstrap.Modal(document.getElementById('supplierModal'));
        modal.hide();
        loadSuppliersPage();
        try { populateStockSelects(); } catch (e) {}
    } catch (err) {
        console.error('saveSupplierFromModal error', err);
        Toast.error(err.message || 'Failed to save supplier');
    } finally {
        LoadingOverlay.hide();
    }
}

async function deleteSupplier(id) {
    if (!confirm('Delete supplier #' + id + '?')) return;
    try {
        LoadingOverlay.show('Deleting supplier...');
        await apiClient.deleteSupplier(id);
        Toast.success('Supplier deleted');
        loadSuppliersPage();
        try { populateStockSelects(); } catch (e) {}
    } catch (err) {
        console.error('deleteSupplier error', err);
        Toast.error(err.message || 'Failed to delete supplier');
    } finally {
        LoadingOverlay.hide();
    }
}

// Service management functions
window._editingServiceId = null;

async function loadServicesPage() {
    try {
        LoadingOverlay.show('Loading services...');
        const resp = await apiClient.getServices();
        const services = Array.isArray(resp) ? resp : resp.services || [];
        const tbody = document.getElementById('servicesTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        services.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.id}</td>
                <td>${s.name}</td>
                <td>${s.price}</td>
                <td>${s.duration_mins} mins</td>
                <td>${s.service_type}</td>
                <td>
                    ${s.image ? `<img src="/static/${s.image}" alt="${s.name}" style="max-width: 50px; max-height: 50px;" class="img-thumbnail">` : 'No image'}
                </td>
                <td>
                    <button class="btn btn-sm btn-primary me-2" onclick="openEditService(${s.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteService(${s.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('loadServicesPage error', err);
        Toast.error('Failed to load services');
    } finally {
        LoadingOverlay.hide();
    }
}

function openAddServiceModal() {
    window._editingServiceId = null;
    document.getElementById('serviceName').value = '';
    document.getElementById('description').value = '';
    document.getElementById('price').value = 0;
    document.getElementById('duration').value = 30;
    document.getElementById('categoryId').value = '';
    document.getElementById('serviceType').value = 'in-center';
    document.getElementById('serviceImage').value = '';
    var modal = new bootstrap.Modal(document.getElementById('addServiceModal'));
    modal.show();
}

function openEditService(id) {
    const rows = document.querySelectorAll('#servicesTableBody tr');
    let found = null;
    rows.forEach(r => {
        const cols = r.querySelectorAll('td');
        if (cols && Number(cols[0].textContent) === Number(id)) {
            found = { 
                id: id, 
                name: cols[1].textContent, 
                price: cols[2].textContent.replace('₹', ''), 
                duration: cols[3].textContent.replace(' mins', ''),
                type: cols[4].textContent
            };
        }
    });
    
    // Fetch full service details for editing
    if (found) {
        fetch(`/api/services/${id}`)
            .then(res => res.json())
            .then(service => {
                window._editingServiceId = id;
                document.getElementById('editServiceName').value = service.name || '';
                document.getElementById('editDescription').value = service.description || '';
                document.getElementById('editPrice').value = parseFloat(service.price) || 0;
                document.getElementById('editDuration').value = service.duration_mins || 30;
                document.getElementById('editCategoryId').value = service.category_id || '';
                document.getElementById('editServiceType').value = service.service_type || 'in-center';
                document.getElementById('editServiceImage').value = '';
                
                // Show current image if exists
                const currentImageContainer = document.getElementById('currentImageContainer');
                const currentImage = document.getElementById('currentServiceImage');
                if (service.image) {
                    currentImage.src = `/static/${service.image}`;
                    currentImageContainer.style.display = 'block';
                } else {
                    currentImageContainer.style.display = 'none';
                }
                
                var modal = new bootstrap.Modal(document.getElementById('editServiceModal'));
                modal.show();
            })
            .catch(err => {
                console.error('Failed to fetch service details', err);
                Toast.error('Failed to load service details');
            });
    }
}

async function saveServiceFromModal() {
    if (window._savingService) return;
    window._savingService = true;
    document.getElementById('saveServiceBtn')?.setAttribute('disabled', 'disabled');

    const formData = new FormData();
    formData.append('name', document.getElementById('serviceName').value.trim());
    formData.append('description', document.getElementById('description').value);
    formData.append('price', document.getElementById('price').value);
    formData.append('duration_mins', document.getElementById('duration').value);
    formData.append('category_id', document.getElementById('categoryId').value || null);
    formData.append('service_type', document.getElementById('serviceType').value);
    
    const imageFile = document.getElementById('serviceImage').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    if (!formData.get('name')) { 
        Toast.error('Name required'); 
        window._savingService = false;
        document.getElementById('saveServiceBtn')?.removeAttribute('disabled');
        return; 
    }

    try {
        LoadingOverlay.show('Saving service...');
        await apiClient.createService(formData);
        Toast.success('Service created');
        var modal = bootstrap.Modal.getInstance(document.getElementById('addServiceModal')) || new bootstrap.Modal(document.getElementById('addServiceModal'));
        modal.hide();
        loadServicesPage();
    } catch (err) {
        console.error('saveServiceFromModal error', err);
        Toast.error(err.message || 'Failed to save service');
    } finally {
        LoadingOverlay.hide();
        window._savingService = false;
        document.getElementById('saveServiceBtn')?.removeAttribute('disabled');
    }
}

async function updateServiceFromModal() {
    if (window._updatingService) return;
    window._updatingService = true;
    document.getElementById('updateServiceBtn')?.setAttribute('disabled', 'disabled');

    const formData = new FormData();
    formData.append('name', document.getElementById('editServiceName').value.trim());
    formData.append('description', document.getElementById('editDescription').value);
    formData.append('price', document.getElementById('editPrice').value);
    formData.append('duration_mins', document.getElementById('editDuration').value);
    formData.append('category_id', document.getElementById('editCategoryId').value || null);
    formData.append('service_type', document.getElementById('editServiceType').value);
    
    const imageFile = document.getElementById('editServiceImage').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    if (!formData.get('name')) { 
        Toast.error('Name required'); 
        window._updatingService = false;
        document.getElementById('updateServiceBtn')?.removeAttribute('disabled');
        return; 
    }

    try {
        LoadingOverlay.show('Updating service...');
        await apiClient.updateService(window._editingServiceId, formData);
        Toast.success('Service updated');
        window._editingServiceId = null;
        var modal = bootstrap.Modal.getInstance(document.getElementById('editServiceModal')) || new bootstrap.Modal(document.getElementById('editServiceModal'));
        modal.hide();
        loadServicesPage();
    } catch (err) {
        console.error('updateServiceFromModal error', err);
        Toast.error(err.message || 'Failed to update service');
    } finally {
        LoadingOverlay.hide();
        window._updatingService = false;
        document.getElementById('updateServiceBtn')?.removeAttribute('disabled');
    }
}

// Package booking details function for admin bills page
async function viewPackageBookingDetails(bookingId) {
    try {
        const response = await apiClient.get(`/api/package/admin/bookings/${bookingId}`);
        const booking = response;

        let details = `Package Booking Details:\n\n`;
        details += `ID: ${booking.id}\n`;
        details += `Customer: ${booking.customer_name || 'N/A'}\n`;
        details += `Package: ${booking.package_name || 'N/A'}\n`;
        details += `Status: ${booking.status}\n`;
        details += `Service Type: ${booking.service_type || 'N/A'}\n`;
        details += `Total Amount: ₹${parseFloat(booking.total_amount || 0).toFixed(2)}\n`;
        details += `Payment Status: ${booking.razorpay_payment_id ? 'Paid' : 'Pending'}\n`;

        if (booking.start_datetime) {
            details += `Start Date/Time: ${new Date(booking.start_datetime).toLocaleString()}\n`;
        }
        if (booking.end_datetime) {
            details += `End Date/Time: ${new Date(booking.end_datetime).toLocaleString()}\n`;
        }
        if (booking.address) {
            details += `Address: ${booking.address}\n`;
        }
        if (booking.pincode) {
            details += `Pincode: ${booking.pincode}\n`;
        }
        if (booking.notes) {
            details += `Notes: ${booking.notes}\n`;
        }

        alert(details);
    } catch (error) {
        console.error('Error loading booking details:', error);
        alert('Failed to load booking details');
    }
}

// Update the initial load to include services
document.addEventListener('DOMContentLoaded', async function() {
    if (!window.apiClient) return;

    if (document.getElementById('offersTableBody')) await loadOffersPage();
    if (document.getElementById('productsTableBody')) await loadProductsPage();
    if (document.getElementById('billsTableBody')) await loadBillsPage();
    if (document.getElementById('packageBookingsTableBody')) await loadPackageBookingsPage();
    if (document.getElementById('complaintsTableBody')) await loadComplaintsPage();
    if (document.getElementById('deliveryOrdersBody')) await loadDeliveryPage();
    if (document.getElementById('ordersTableBody')) await loadOrdersPage();
    if (document.getElementById('customersTableBody')) await loadCustomersPage();
    if (document.getElementById('usersTableBody')) await loadUsersPage();
    if (document.getElementById('staffTableBody')) await loadStaffPage();
    if (document.getElementById('brandsTableBody')) await loadBrandsPage();
    if (document.getElementById('appointmentsTableBody')) await loadAppointmentsPage();
    if (document.getElementById('stockTableBody')) await loadStockPage();
    if (document.getElementById('suppliersTableBody')) await loadSuppliersPage();
    if (document.getElementById('servicesTableBody')) await loadServicesPage();
    if (document.getElementById('stockTableBody')) await populateStockSelects();
});
